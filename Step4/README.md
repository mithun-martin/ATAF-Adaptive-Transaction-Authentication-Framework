# Step 4 — Collect and Prepare the Dataset

This step automates the data engineering pipeline for the **IEEE-CIS Fraud Detection** dataset. 

Because the dataset is hosted as a Kaggle competition and requires accepting their specific terms of service, **you must download the raw files manually** before running the processing pipeline.

## 1. Download the Dataset
1. Go to the [IEEE-CIS Fraud Detection Kaggle Page](https://www.kaggle.com/c/ieee-fraud-detection/data).
2. Accept the competition rules and download the dataset.
3. Extract the contents and place `train_transaction.csv` and `train_identity.csv` into the `data/raw/` folder in this directory.

```text
Step4/
├── data/
│   ├── raw/
│   │   ├── train_transaction.csv   <-- Place here
│   │   └── train_identity.csv      <-- Place here
│   └── processed/                  <-- Output goes here
├── prepare_dataset.py
└── requirements.txt
```

## 2. Run the Processing Pipeline
The `prepare_dataset.py` script automatically performs the following tasks outlined in the project plan:
- **Memory Reduction:** Downcasts numerical types to fit the massive dataset into RAM.
- **Data Cleaning:** Merges the tables and drops columns with >80% missing data.
- **Missing Value Handling:** Imputes medians for numericals and 'Missing' for categoricals.
- **Encoding:** Uses Label Encoding for categorical features.
- **Train/Validation/Test Split:** Splits the data (70% Train, 15% Validation, 15% Test) using stratified sampling.
- **Class Imbalance Handling:** Applies **SMOTE** (Synthetic Minority Over-sampling Technique) strictly on the Training set to avoid data leakage while providing enough fraud examples for the ML models.
- **Parquet Export:** Saves the final datasets as highly compressed Parquet files.

### Setup and Execution
Open a terminal in the `Step4` folder and run:
```powershell
# Create a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run the pipeline
python prepare_dataset.py
```

The script will output `train_processed.parquet`, `val_processed.parquet`, and `test_processed.parquet` into the `data/processed/` folder. These files will be used by Mithun in **Step 5** to train the AI Risk Models.
