"""
Step 10: Data Models for Social-Engineering Attack Scenarios
=============================================================
Defines schemas for attack categories, attacker profiles, transaction
contexts, and simulation outcome evaluation.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AttackCategory(str, Enum):
    OTP_HARVESTING = "OTP_HARVESTING"                   # Classic vishing / OTP deception
    BENEFICIARY_MULE = "BENEFICIARY_MULE"               # Urgent transfer to freshly added mule account
    REMOTE_ACCESS_TAKEOVER = "REMOTE_ACCESS_TAKEOVER"   # Remote desktop tool (AnyDesk/TeamViewer)
    OFF_HOURS_COERCION = "OFF_HOURS_COERCION"           # Late night coercion (01:00-05:00)
    VOLUME_ANOMALY = "VOLUME_ANOMALY"                   # Severe balance drain / volume deviation
    COMPOUND_SUSPICIOUS = "COMPOUND_SUSPICIOUS"         # Multiple simultaneous red flags
    BENIGN_CONTROL = "BENIGN_CONTROL"                   # Legitimate baseline transfer (usability control)


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AttackerProfile(BaseModel):
    mitre_attack_technique: str = Field(..., description="MITRE ATT&CK technique reference, e.g. T1566.002")
    pretext: str = Field(..., description="Social-engineering storyline used by attacker")
    delivery_channel: str = Field(..., description="Vishing, WhatsApp, Remote Session, SMS, Email")
    victim_psychological_state: str = Field(..., description="Coerced/Panic, Compliant/Trusting, Distracted")


class TransactionContext(BaseModel):
    amount: float = Field(..., gt=0, description="Transfer amount in INR")
    user_avg_amount: float = Field(default=5000.0, description="Sender's historical typical transaction amount")
    is_new_beneficiary: bool = Field(default=False, description="Whether recipient was added in last 24h")
    beneficiary_name: str = Field(..., description="Recipient contact name")
    beneficiary_account: str = Field(..., description="Destination account number")
    hour_of_day: int = Field(default=12, ge=0, le=23, description="Hour of initiation (0 to 23)")
    velocity_last_hour: int = Field(default=0, ge=0, description="Transfers initiated in previous 60 minutes")
    is_new_device: bool = Field(default=False, description="Initiated from unrecognized client hardware/IP")
    victim_provides_otp: bool = Field(default=True, description="Whether victim is deceived into sharing/entering OTP")
    victim_heeds_warning_banner: bool = Field(default=True, description="Whether an anti-social-engineering warning banner makes victim pause")
    victim_signs_affirmation: bool = Field(default=False, description="Whether victim knowingly signs anti-coercion confirmation on high-risk prompt")
    victim_knows_pin: bool = Field(default=True, description="Whether secret transaction PIN is available")


class SystemExpectation(BaseModel):
    expected_authorized: bool = Field(..., description="Whether system is expected to approve transaction")
    expected_factors: List[str] = Field(..., description="List of factors expected to be enforced")
    expected_defense_outcome: str = Field(..., description="Summary of security outcome")
    expected_friction_steps: int = Field(..., description="Count of authentication steps required")


class AttackScenario(BaseModel):
    id: str = Field(..., description="Unique scenario identifier, e.g. SCN-01")
    name: str = Field(..., description="Concise human-readable scenario name")
    category: AttackCategory = Field(..., description="Categorized fraud pattern")
    severity: SeverityLevel = Field(..., description="Threat severity level")
    is_fraud: bool = Field(..., description="True for simulated attacks, False for benign controls")
    description: str = Field(..., description="Detailed narrative of the attack scenario")
    attacker_profile: AttackerProfile = Field(..., description="Threat actor strategy and pretext")
    transaction: TransactionContext = Field(..., description="Transaction parameter payload")
    expectations: Dict[str, SystemExpectation] = Field(
        ..., description="Expected behavior across System 1, System 2, and System 3"
    )


class SystemEvaluationOutcome(BaseModel):
    system_name: str
    authorized: bool
    fraud_prevented: bool
    risk_tier: Optional[str] = None
    risk_score: Optional[float] = None
    factors_enforced: List[str]
    friction_steps: int
    security_verdict: str  # e.g., "COMPROMISED", "PREVENTED", "BENIGN_AUTHORIZED", "FALSE_POSITIVE"
    explanation: str


class ScenarioExecutionReport(BaseModel):
    scenario_id: str
    scenario_name: str
    category: AttackCategory
    is_fraud: bool
    severity: SeverityLevel
    system_1_baseline: SystemEvaluationOutcome
    system_2_static_3fa: SystemEvaluationOutcome
    system_3_adaptive: SystemEvaluationOutcome
