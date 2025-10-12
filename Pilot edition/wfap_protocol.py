"""
Wells Fargo Agent Protocol (WFAP) Models
Defines the data structures for Intent and Offer communication between agents.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import hashlib


@dataclass
class Consumer:
    """Company information for credit requests."""
    company_id: str
    company_name: str
    credit_score: int
    annual_revenue: float
    years_in_business: int
    industry: str


@dataclass
class CreditRequest:
    """Credit request details."""
    amount: float
    duration: int  # months
    purpose: str
    preferred_interest_rate: Optional[float] = None


@dataclass
class ESGRequirements:
    """ESG requirements for the credit request."""
    esg_weight: float = 0.3  # Weight given to ESG factors (0-1)
    carbon_footprint_threshold: Optional[float] = None
    social_impact_focus: List[str] = None

    def __post_init__(self):
        if self.social_impact_focus is None:
            self.social_impact_focus = []


@dataclass
class DigitalSignature:
    """Digital signature for authentication."""
    algorithm: str
    signature: str
    public_key: str


@dataclass
class Intent:
    """Credit request intent sent by consumer agent."""
    request_id: str
    timestamp: datetime
    consumer: Consumer
    credit_request: CreditRequest
    esg_requirements: Optional[ESGRequirements] = None
    digital_signature: Optional[DigitalSignature] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Handle timestamp serialization safely
        if hasattr(self.timestamp, 'isoformat'):
            data['timestamp'] = self.timestamp.isoformat()
        else:
            data['timestamp'] = str(self.timestamp)
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Intent':
        """Create Intent from dictionary."""
        # Skip timestamp validation - use whatever value is provided
        if data.get('esg_requirements'):
            data['esg_requirements'] = ESGRequirements(**data['esg_requirements'])
        if data.get('digital_signature'):
            data['digital_signature'] = DigitalSignature(**data['digital_signature'])
        data['consumer'] = Consumer(**data['consumer'])
        data['credit_request'] = CreditRequest(**data['credit_request'])
        return cls(**data)

    def create_signature(self, private_key: str = "default_key") -> None:
        """Create a simple digital signature for the intent."""
        content = f"{self.request_id}{self.timestamp.isoformat()}{self.consumer.company_id}"
        signature = hashlib.sha256(f"{content}{private_key}".encode()).hexdigest()
        self.digital_signature = DigitalSignature(
            algorithm="SHA256",
            signature=signature,
            public_key=f"public_{private_key}"
        )


@dataclass
class Bank:
    """Bank information."""
    bank_id: str
    bank_name: str
    bank_token: str
    regulatory_license: str


@dataclass
class OfferTerms:
    """Terms of the credit offer."""
    approved_amount: float
    interest_rate: float  # Annual percentage
    repayment_period: int  # months
    origination_fee: float = 0.0
    annual_fee: float = 0.0
    drawing_period: int = 12  # months


@dataclass
class ESGImpact:
    """ESG impact assessment."""
    carbon_footprint: float
    carbon_adjusted_rate: float
    esg_score: int  # 0-100
    esg_summary: str
    sustainability_initiatives: List[str] = None

    def __post_init__(self):
        if self.sustainability_initiatives is None:
            self.sustainability_initiatives = []


@dataclass
class ComplianceCheck:
    """Individual compliance check result."""
    check_type: str
    status: str  # "passed", "failed", "warning"
    details: Optional[str] = None


@dataclass
class RiskAssessment:
    """Risk assessment for the offer."""
    risk_level: str  # "low", "medium", "high"
    risk_factors: List[str] = None

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []


@dataclass
class RegulatoryCompliance:
    """Regulatory compliance information."""
    compliance_checks: List[ComplianceCheck]
    risk_assessment: RiskAssessment


@dataclass
class Offer:
    """Credit offer from bank agent."""
    offer_id: str
    request_id: str
    timestamp: datetime
    bank: Bank
    offer_terms: OfferTerms
    esg_impact: ESGImpact
    regulatory_compliance: RegulatoryCompliance
    digital_signature: Optional[DigitalSignature] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Handle timestamp serialization safely
        if hasattr(self.timestamp, 'isoformat'):
            data['timestamp'] = self.timestamp.isoformat()
        else:
            data['timestamp'] = str(self.timestamp)
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Offer':
        """Create Offer from dictionary."""
        # Skip timestamp validation - use whatever value is provided
        if data.get('digital_signature'):
            data['digital_signature'] = DigitalSignature(**data['digital_signature'])
        data['bank'] = Bank(**data['bank'])
        data['offer_terms'] = OfferTerms(**data['offer_terms'])
        data['esg_impact'] = ESGImpact(**data['esg_impact'])
        
        # Handle compliance checks
        compliance_checks = [ComplianceCheck(**check) for check in data['regulatory_compliance']['compliance_checks']]
        risk_assessment = RiskAssessment(**data['regulatory_compliance']['risk_assessment'])
        data['regulatory_compliance'] = RegulatoryCompliance(
            compliance_checks=compliance_checks,
            risk_assessment=risk_assessment
        )
        
        return cls(**data)

    def create_signature(self, private_key: str = "default_key") -> None:
        """Create a simple digital signature for the offer."""
        content = f"{self.offer_id}{self.request_id}{self.timestamp.isoformat()}{self.bank.bank_id}"
        signature = hashlib.sha256(f"{content}{private_key}".encode()).hexdigest()
        self.digital_signature = DigitalSignature(
            algorithm="SHA256",
            signature=signature,
            public_key=f"public_{private_key}"
        )

    def calculate_total_cost(self) -> float:
        """Calculate total cost including fees."""
        base_cost = self.offer_terms.approved_amount * (self.offer_terms.interest_rate / 100)
        total_fees = self.offer_terms.origination_fee + self.offer_terms.annual_fee
        return base_cost + total_fees

    def calculate_carbon_adjusted_rate(self) -> float:
        """Calculate carbon-adjusted interest rate."""
        carbon_penalty = self.esg_impact.carbon_footprint * 0.01  # 0.01% per carbon unit
        return self.offer_terms.interest_rate + carbon_penalty


def verify_signature(data: Dict[str, Any], expected_public_key: str) -> bool:
    """Verify digital signature of intent or offer."""
    # Simplified verification - in real implementation, use proper cryptographic verification
    if not data.get('digital_signature'):
        return False
    
    signature = data['digital_signature']
    # Handle both dict and DigitalSignature object
    if hasattr(signature, 'algorithm'):
        # It's a DigitalSignature object
        return signature.algorithm == "SHA256" and signature.public_key == expected_public_key
    else:
        # It's a dictionary
        return signature['algorithm'] == "SHA256" and signature['public_key'] == expected_public_key
