import os
import gc
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline

# Configuration
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
TRANSACTION_FILE = os.path.join(RAW_DIR, "train_transaction.csv")
IDENTITY_FILE = os.path.join(RAW_DIR, "train_identity.csv")

def reduce_mem_usage(df):
    """Iterate through all columns of a dataframe and modify the data type to reduce memory usage."""
    start_mem = df.memory_usage().sum() / 1024**2
    print(f"Memory usage of dataframe is {start_mem:.2f} MB")
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != object:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)  
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
    
    end_mem = df.memory_usage().sum() / 1024**2
    print(f"Memory usage after optimization is: {end_mem:.2f} MB")
    print(f"Decreased by {100 * (start_mem - end_mem) / start_mem:.1f}%")
    return df

def load_and_merge_data():
    print("Loading data in chunks to save memory...")
    if not os.path.exists(TRANSACTION_FILE) or not os.path.exists(IDENTITY_FILE):
        raise FileNotFoundError(f"Please download the dataset from Kaggle and place train_transaction.csv and train_identity.csv in {RAW_DIR}")
        
    trans_chunks = []
    for chunk in pd.read_csv(TRANSACTION_FILE, chunksize=100000):
        trans_chunks.append(reduce_mem_usage(chunk))
    df_trans = pd.concat(trans_chunks, ignore_index=True)
    del trans_chunks
    gc.collect()

    id_chunks = []
    for chunk in pd.read_csv(IDENTITY_FILE, chunksize=100000):
        id_chunks.append(reduce_mem_usage(chunk))
    df_id = pd.concat(id_chunks, ignore_index=True)
    del id_chunks
    gc.collect()
    
    print("Merging data...")
    df = pd.merge(df_trans, df_id, on='TransactionID', how='left')
    del df_trans, df_id
    gc.collect()
    
    df = reduce_mem_usage(df)
    return df

def clean_and_impute(df):
    print("Cleaning data & handling missing values...")
    
    # 1. Drop columns with more than 80% missing values to reduce noise
    missing_pct = df.isnull().sum() / len(df)
    cols_to_drop = missing_pct[missing_pct > 0.8].index
    df = df.drop(columns=cols_to_drop)
    
    # 2. Separate numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.drop(['TransactionID', 'isFraud'])
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns
    
    # 3. Impute missing values
    print("Imputing numeric columns with median...")
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())
        
    print("Imputing categorical columns with 'Missing'...")
    for col in categorical_cols:
        df[col] = df[col].fillna('Missing')
        
    return df, categorical_cols

def encode_features(df, categorical_cols):
    print("Encoding categorical features...")
    le = LabelEncoder()
    
    for col in categorical_cols:
        df[col] = le.fit_transform(df[col].astype(str))
        
    return df

def split_and_balance(df):
    print("Splitting dataset into Train/Val/Test (70/15/15)...")
    
    # Drop TransactionID and extract target
    X = df.drop(columns=['TransactionID', 'isFraud'])
    y = df['isFraud']
    
    # First split: 70% Train, 30% Temp (Val + Test)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    # Second split: Split Temp into 15% Val, 15% Test
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    
    print(f"Original training shape: {X_train.shape}, Class distribution: \n{y_train.value_counts()}")
    
    # Step 1: Undersample majority class down to 10x the minority count (saves memory)
    # Step 2: Oversample minority class up to 1:3 ratio using simple duplication (no KNN needed)
    # This is far lighter than SMOTE which needs to fit KNN across 358 features
    minority_count = y_train.sum()
    majority_target = int(minority_count * 10)   # majority -> 10x minority
    minority_target = int(minority_count * 3)     # minority -> 3x (1:3.3 ratio after step1)

    pipeline = ImbPipeline([
        ('under', RandomUnderSampler(sampling_strategy={0: majority_target}, random_state=42)),
        ('over',  RandomOverSampler(sampling_strategy={1: minority_target}, random_state=42)),
    ])
    X_train_res, y_train_res = pipeline.fit_resample(X_train, y_train)
    del X_train, y_train
    gc.collect()
    
    print(f"Balanced training shape: {X_train_res.shape}, Class distribution: \n{pd.Series(y_train_res).value_counts()}")
    
    return X_train_res, X_val, X_test, y_train_res, y_val, y_test

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # 1. Load Data
    df = load_and_merge_data()
    
    # 2. Clean & Impute
    df, cat_cols = clean_and_impute(df)
    
    # 3. Feature Encoding
    df = encode_features(df, cat_cols)
    
    # 4. Split & Balance
    X_train, X_val, X_test, y_train, y_val, y_test = split_and_balance(df)
    
    # 5. Save Output
    print("Saving processed datasets...")
    
    train_df = pd.concat([X_train, y_train], axis=1)
    val_df = pd.concat([X_val, y_val], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    
    train_df.to_parquet(os.path.join(PROCESSED_DIR, "train_processed.parquet"), index=False)
    val_df.to_parquet(os.path.join(PROCESSED_DIR, "val_processed.parquet"), index=False)
    test_df.to_parquet(os.path.join(PROCESSED_DIR, "test_processed.parquet"), index=False)
    
    print(f"Done! Files saved in {PROCESSED_DIR} as Parquet files (to save space).")

if __name__ == "__main__":
    main()
