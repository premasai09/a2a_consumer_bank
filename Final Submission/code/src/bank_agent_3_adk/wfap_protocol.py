from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import hashlib
from enum import Enum

# === Bank Internal Policies Configuration for Corporate Line of Credit Evaluation ===

class IndustryRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    VERY_HIGH = "very_high"

class CreditRating(Enum):
    EXCELLENT = "excellent"  # 750+
    GOOD = "good"           # 650-749
    FAIR = "fair"           # 550-649
    POOR = "poor"           # Below 550

class CollateralType(Enum):
    REAL_ESTATE = "real_estate"
    EQUIPMENT = "equipment"
    INVENTORY = "inventory"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    SECURITIES = "securities"
    CASH_DEPOSITS = "cash_deposits"

@dataclass
class BankPoliciesConfig:
    """Configuration class containing all bank internal policies for line of credit evaluation"""
    # MINIMUM ELIGIBILITY CRITERIA - AGGRESSIVE BANK
    min_annual_revenue: float = 500_000.0  # Minimum $500K annual revenue
    min_years_in_business: int = 1  # Minimum 1 year in operation
    min_credit_score: int = 550  # Minimum business credit score
    min_debt_service_coverage_ratio: float = 1.1  # Minimum DSCR
    max_debt_to_equity_ratio: float = 6.0  # Maximum debt-to-equity ratio
    min_current_ratio: float = 1.0  # Minimum current ratio (current assets/current liabilities)
    # CREDIT LIMIT CALCULATIONS - AGGRESSIVE BANK
    max_credit_limit_percentage_of_revenue: float = 0.25  # Max 25% of annual revenue
    max_credit_limit_absolute: float = 15_000_000.0  # Maximum $15M credit limit
    min_credit_limit: float = 50_000.0  # Minimum $50K credit limit
    # DYNAMIC LENDING RATIO MODEL - AGGRESSIVE BANK
    base_lending_ratio: float = 0.25  # Base 25% of annual revenue for lending decisions
    # REPAYMENT DURATION POLICIES
    loan_purpose_duration_limits: Dict[str, Dict[str, int]] = None
    # INTEREST RATES AND FEES (Annual Percentage) - AGGRESSIVE BANK
    base_interest_rate: float = 9.5  # Base rate
    risk_premium_rates: Dict[IndustryRiskLevel, float] = None
    credit_score_adjustments: Dict[CreditRating, float] = None
    # COLLATERAL REQUIREMENTS - AGGRESSIVE BANK
    min_collateral_coverage_ratio: float = 1.2  # 120% collateral coverage
    acceptable_collateral_types: List[CollateralType] = None
    collateral_valuation_discount_rates: Dict[CollateralType, float] = None
    # INDUSTRY RISK CLASSIFICATIONS
    industry_risk_levels: Dict[str, IndustryRiskLevel] = None
    prohibited_industries: List[str] = None
    # FINANCIAL RATIO REQUIREMENTS - AGGRESSIVE BANK
    max_leverage_ratio: float = 8.0  # Maximum total debt / EBITDA
    min_interest_coverage_ratio: float = 1.8  # EBITDA / Interest Expense
    min_quick_ratio: float = 0.8  # (Current Assets - Inventory) / Current Liabilities
    max_accounts_receivable_days: int = 120  # Maximum days sales outstanding
    # DOCUMENTATION REQUIREMENTS - AGGRESSIVE BANK
    required_financial_statements_years: int = 2
    required_tax_returns_years: int = 2
    audit_requirement_threshold: float = 10_000_000.0  # Audited statements required for >$10M revenue
    # APPROVAL LIMITS (by credit officer level)
    approval_limits: Dict[str, float] = None
    # MONITORING AND COVENANTS - AGGRESSIVE BANK
    financial_covenant_testing_frequency: str = "semi-annually"
    required_financial_reporting_frequency: str = "quarterly"
    site_visit_requirement_threshold: float = 5_000_000.0  # Site visit required for >$5M requests
    # PERSONAL GUARANTY REQUIREMENTS - AGGRESSIVE BANK
    personal_guaranty_threshold: float = 1_000_000.0  # Required for loans >$1M
    min_personal_credit_score_guarantor: int = 600
    max_guarantor_age: int = 75
    def __post_init__(self):
        if self.risk_premium_rates is None:
            self.risk_premium_rates = {
                IndustryRiskLevel.LOW: 0.0,
                IndustryRiskLevel.MEDIUM: 0.5,
                IndustryRiskLevel.HIGH: 1.0,
                IndustryRiskLevel.VERY_HIGH: 2.0
            }
        if self.credit_score_adjustments is None:
            self.credit_score_adjustments = {
                CreditRating.EXCELLENT: -0.75,
                CreditRating.GOOD: -0.25,
                CreditRating.FAIR: 0.5,
                CreditRating.POOR: 1.5
            }
        if self.acceptable_collateral_types is None:
            self.acceptable_collateral_types = [
                CollateralType.REAL_ESTATE,
                CollateralType.EQUIPMENT,
                CollateralType.ACCOUNTS_RECEIVABLE,
                CollateralType.SECURITIES,
                CollateralType.CASH_DEPOSITS
            ]
        if self.collateral_valuation_discount_rates is None:
            self.collateral_valuation_discount_rates = {
                CollateralType.REAL_ESTATE: 0.15,
                CollateralType.EQUIPMENT: 0.25,
                CollateralType.INVENTORY: 0.40,
                CollateralType.ACCOUNTS_RECEIVABLE: 0.10,
                CollateralType.SECURITIES: 0.20,
                CollateralType.CASH_DEPOSITS: 0.0
            }
        if self.industry_risk_levels is None:
            self.industry_risk_levels = {
                "healthcare_services": IndustryRiskLevel.LOW,
                "utilities": IndustryRiskLevel.LOW,
                "food_processing": IndustryRiskLevel.LOW,
                "professional_services": IndustryRiskLevel.LOW,
                "technology_software": IndustryRiskLevel.LOW,
                "manufacturing": IndustryRiskLevel.MEDIUM,
                "retail_trade": IndustryRiskLevel.MEDIUM,
                "transportation": IndustryRiskLevel.MEDIUM,
                "construction": IndustryRiskLevel.MEDIUM,
                "wholesale_trade": IndustryRiskLevel.MEDIUM,
                "oil_gas": IndustryRiskLevel.HIGH,
                "mining": IndustryRiskLevel.HIGH,
                "agriculture": IndustryRiskLevel.HIGH,
                "hospitality": IndustryRiskLevel.HIGH,
                "real_estate": IndustryRiskLevel.HIGH,
                "cryptocurrency": IndustryRiskLevel.VERY_HIGH,
                "gambling": IndustryRiskLevel.VERY_HIGH,
                "adult_entertainment": IndustryRiskLevel.VERY_HIGH,
                "cannabis": IndustryRiskLevel.VERY_HIGH
            }
        if self.prohibited_industries is None:
            self.prohibited_industries = [
                "illegal_activities",
                "money_laundering",
                "terrorist_financing"
            ]
        if self.approval_limits is None:
            self.approval_limits = {
                "loan_officer": 500_000.0,
                "senior_loan_officer": 1_000_000.0,
                "credit_manager": 2_000_000.0,
                "senior_credit_manager": 5_000_000.0,
                "chief_credit_officer": 10_000_000.0,
                "loan_committee": 15_000_000.0
            }
        if self.loan_purpose_duration_limits is None:
            self.loan_purpose_duration_limits = {
                "working_capital": {"max_duration": 36, "min_duration": 12},
                "working capital": {"max_duration": 36, "min_duration": 12},
                "inventory_financing": {"max_duration": 24, "min_duration": 6},
                "inventory financing": {"max_duration": 24, "min_duration": 6},
                "equipment_purchase": {"max_duration": 60, "min_duration": 24},
                "equipment purchase": {"max_duration": 60, "min_duration": 24},
                "business_expansion": {"max_duration": 84, "min_duration": 36},
                "business expansion": {"max_duration": 84, "min_duration": 36},
                "general_business_purposes": {"max_duration": 48, "min_duration": 12},
                "general business purposes": {"max_duration": 48, "min_duration": 12},
                "cash_flow_management": {"max_duration": 24, "min_duration": 6},
                "cash flow management": {"max_duration": 24, "min_duration": 6},
                "seasonal_financing": {"max_duration": 18, "min_duration": 3},
                "seasonal financing": {"max_duration": 18, "min_duration": 3},
                "bridge_financing": {"max_duration": 12, "min_duration": 3},
                "bridge financing": {"max_duration": 12, "min_duration": 3},
                "acquisition_financing": {"max_duration": 72, "min_duration": 24},
                "acquisition financing": {"max_duration": 72, "min_duration": 24},
                "refinancing": {"max_duration": 60, "min_duration": 12},
                "debt_consolidation": {"max_duration": 60, "min_duration": 12},
                "debt consolidation": {"max_duration": 60, "min_duration": 12}
            }

# REQUIRED APPLICATION FIELDS
class RequiredApplicationFields:
    """Defines all required fields for a corporate line of credit application"""
    # COMPANY INFORMATION
    COMPANY_INFO = {
        "legal_business_name": str,
        "dba_name": str,
        "business_address": dict,
        "mailing_address": dict,
        "employer_identification_number": str,
        "date_established": str,
        "state_of_incorporation": str,
        "business_structure": str,
        "industry_classification": str,
        "industry_description": str,
        "number_of_employees": int,
        "business_website": str,
        "primary_business_activity": str
    }
    # FINANCIAL INFORMATION (Last 3 Years)
    FINANCIAL_INFO = {
        "annual_revenue": List[float],
        "net_income": List[float],
        "total_assets": List[float],
        "total_liabilities": List[float],
        "current_assets": float,
        "current_liabilities": float,
        "cash_and_equivalents": float,
        "accounts_receivable": float,
        "inventory": float,
        "accounts_payable": float,
        "long_term_debt": float,
        "shareholders_equity": float,
        "ebitda": List[float],
        "working_capital": float,
        "monthly_cash_flow": List[float]
    }
    # CREDIT INFORMATION
    CREDIT_INFO = {
        "business_credit_score": int,
        "credit_bureau_reports": List[dict],
        "existing_credit_lines": List[dict],
        "existing_loans": List[dict],
        "loan_payment_history": List[dict],
        "bankruptcy_history": List[dict],
        "legal_judgments": List[dict],
        "tax_liens": List[dict],
        "previous_defaults": List[dict]
    }
    # MANAGEMENT INFORMATION
    MANAGEMENT_INFO = {
        "key_executives": List[dict],
        "ownership_structure": List[dict],
        "board_of_directors": List[dict],
        "management_experience": dict,
        "succession_plan": str,
        "key_person_insurance": List[dict]
    }
    # PERSONAL GUARANTOR INFORMATION (for owners with >20% ownership)
    GUARANTOR_INFO = {
        "personal_credit_scores": List[int],
        "personal_financial_statements": List[dict],
        "personal_tax_returns": List[dict],
        "personal_assets": List[dict],
        "personal_liabilities": List[dict],
        "personal_income": List[dict],
        "guarantor_agreements": List[dict]
    }
    # COLLATERAL INFORMATION
    COLLATERAL_INFO = {
        "offered_collateral": List[dict],
        "real_estate_properties": List[dict],
        "equipment_list": List[dict],
        "inventory_details": dict,
        "accounts_receivable_aging": dict,
        "securities_portfolio": List[dict],
        "deposit_accounts": List[dict],
        "insurance_coverage": List[dict],
        "appraisals": List[dict]
    }
    # LOAN REQUEST DETAILS
    LOAN_REQUEST = {
        "requested_credit_limit": float,
        "intended_use_of_funds": str,
        "repayment_source": str,
        "repayment_schedule": dict,
        "requested_terms": dict,
        "seasonal_variations": dict,
        "projected_usage_pattern": dict,
        "backup_repayment_source": str
    }
    # SUPPORTING DOCUMENTATION
    REQUIRED_DOCUMENTS = {
        "financial_statements": List[dict],
        "tax_returns": List[dict],
        "interim_financial_statements": dict,
        "cash_flow_projections": dict,
        "business_plan": dict,
        "articles_of_incorporation": dict,
        "operating_agreement": dict,
        "corporate_bylaws": dict,
        "board_resolutions": List[dict],
        "insurance_certificates": List[dict],
        "legal_opinions": List[dict],
        "environmental_assessments": List[dict],
        "regulatory_compliance_certificates": List[dict]
    }
    # BANK RELATIONSHIP INFORMATION
    BANK_RELATIONSHIP = {
        "existing_accounts": List[dict],
        "account_activity": dict,
        "previous_credit_applications": List[dict],
        "relationship_length": int,
        "other_bank_relationships": List[dict],
        "primary_banking_relationship": str,
        "deposit_balances": dict,
        "fee_income_generated": dict
    }

# Create the default configuration instance
BANK_POLICIES = BankPoliciesConfig()

# Validation rules for application completeness
VALIDATION_RULES = {
    "required_fields_completion": 0.95,
    "financial_data_consistency": True,
    "document_authenticity_check": True,
    "credit_bureau_verification": True,
    "collateral_verification": True,
    "personal_guaranty_execution": True,
    "regulatory_compliance_check": True,
    "anti_money_laundering_check": True,
    "sanctions_screening": True
}

@dataclass
class Consumer:
    """Company information for credit requests."""
    company_id: str
    company_name: str
    credit_score: int
    annual_revenue: float
    years_in_business: int
    industry: str
    tax_id: str
    jurisdiction: str
    registration_number: str
    contact_email: str
    net_income: float
    assets_total: float
    liabilities_total: float
    credit_report_ref: str
    esg_certifications: str
    esg_reporting_url: str
    regulatory_context_jurisdiction: str
    regulatory_context_related_disclosure: str
    data_sharing_consent: bool
    signature: str


@dataclass
class CreditRequest:
    """Credit request details."""
    amount: float
    duration: int  # months
    purpose: str
    preferred_interest_rate: Optional[float] = None
    repayment_preference: Optional[str] = None
    drawdown_type: Optional[str] = None
    collateral_description: Optional[str] = None


@dataclass
class ESGRequirements:
    """ESG requirements for the credit request."""
    esg_weight: float = 0.3  # Weight given to ESG factors (0-1)
    carbon_footprint_threshold: Optional[float] = None
    social_impact_focus: List[str] = None
    esg_certifications: Optional[str] = None
    esg_reporting_url: Optional[str] = None
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
    protocol_version: str = "WFAP-1.0"
    sender_id: str = ""
    sender_name: str = ""
    sender_contact_email: str = ""
    signature: str = ""
    yearsinbusiness: Optional[int] = None
    ESG_impact_ratio: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization, flattening for compatibility with new JSON structure."""
        data = asdict(self)
        # Flatten nested objects for compatibility with new JSON structure
        data['intent_id'] = self.request_id
        data['created_at'] = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
        data['amount_value'] = self.credit_request.amount
        data['repayment_duration'] = self.credit_request.duration
        data['purpose'] = self.credit_request.purpose
        data['preferred_interest_rate'] = self.credit_request.preferred_interest_rate
        data['repayment_preference'] = self.credit_request.repayment_preference
        data['drawdown_type'] = self.credit_request.drawdown_type
        data['collateral_description'] = self.credit_request.collateral_description
        # Consumer fields
        data['sender_name'] = self.consumer.company_name
        data['sender_id'] = self.consumer.company_id
        data['sender_contact_email'] = self.consumer.contact_email
        data['company_registration_number'] = self.consumer.registration_number
        data['jurisdiction'] = self.consumer.jurisdiction
        data['industry_code'] = self.consumer.industry
        data['tax_id'] = self.consumer.tax_id
        data['financials'] = {
            "annual_revenue": self.consumer.annual_revenue,
            "net_income": self.consumer.net_income,
            "assets_total": self.consumer.assets_total,
            "liabilities_total": self.consumer.liabilities_total,
        }
        data['credit_report_ref'] = self.consumer.credit_report_ref
        data['esg_certifications'] = self.consumer.esg_certifications
        data['esg_reporting_url'] = self.consumer.esg_reporting_url
        data['regulatory_context_jurisdiction'] = self.consumer.regulatory_context_jurisdiction
        data['regulatory_context_related_disclosure'] = self.consumer.regulatory_context_related_disclosure
        data['data_sharing_consent'] = self.consumer.data_sharing_consent
        data['signature'] = self.consumer.signature
        data['yearsinbusiness'] = self.yearsinbusiness
        data['ESG_impact_ratio'] = self.ESG_impact_ratio
        # Remove nested objects to avoid duplication
        data.pop('consumer', None)
        data.pop('credit_request', None)
        data.pop('request_id', None)
        data.pop('timestamp', None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Intent':
        """Create Intent from dictionary, handling both flat and nested structures."""
        # Handle timestamp
        timestamp = data.get('created_at') or data.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except Exception:
                timestamp = datetime.now()
        # Consumer
        consumer_fields = {
            "company_id": data.get("sender_id") or data.get("company_id"),
            "company_name": data.get("sender_name") or data.get("company_name"),
            "credit_score": data.get("credit_score", 0),
            "annual_revenue": data.get("financials", {}).get("annual_revenue", data.get("annual_revenue", 0.0)),
            "years_in_business": data.get("yearsinbusiness", 0),
            "industry": data.get("industry_code", ""),
            "tax_id": data.get("tax_id", ""),
            "jurisdiction": data.get("jurisdiction", ""),
            "registration_number": data.get("company_registration_number", ""),
            "contact_email": data.get("sender_contact_email", ""),
            "net_income": data.get("financials", {}).get("net_income", data.get("net_income", 0.0)),
            "assets_total": data.get("financials", {}).get("assets_total", data.get("assets_total", 0.0)),
            "liabilities_total": data.get("financials", {}).get("liabilities_total", data.get("liabilities_total", 0.0)),
            "credit_report_ref": data.get("credit_report_ref", ""),
            "esg_certifications": data.get("esg_certifications", ""),
            "esg_reporting_url": data.get("esg_reporting_url", ""),
            "regulatory_context_jurisdiction": data.get("regulatory_context_jurisdiction", ""),
            "regulatory_context_related_disclosure": data.get("regulatory_context_related_disclosure", ""),
            "data_sharing_consent": data.get("data_sharing_consent", False),
            "signature": data.get("signature", ""),
        }
        consumer = Consumer(**consumer_fields)
        # CreditRequest
        credit_request_fields = {
            "amount": data.get("amount_value", 0.0),
            "duration": data.get("repayment_duration", 0),
            "purpose": data.get("purpose", ""),
            "preferred_interest_rate": data.get("preferred_interest_rate"),
            "repayment_preference": data.get("repayment_preference"),
            "drawdown_type": data.get("drawdown_type"),
            "collateral_description": data.get("collateral_description"),
        }
        credit_request = CreditRequest(**credit_request_fields)
        # ESG Requirements
        esg_requirements = None
        if data.get('esg_requirements'):
            esg_requirements = ESGRequirements(**data['esg_requirements'])
        # Digital Signature
        digital_signature = None
        if data.get('digital_signature'):
            digital_signature = DigitalSignature(**data['digital_signature'])
        # Compose Intent
        return cls(
            request_id=data.get("intent_id") or data.get("request_id"),
            timestamp=timestamp,
            consumer=consumer,
            credit_request=credit_request,
            esg_requirements=esg_requirements,
            digital_signature=digital_signature,
            protocol_version=data.get("protocol_version", "WFAP-1.0"),
            sender_id=data.get("sender_id", ""),
            sender_name=data.get("sender_name", ""),
            sender_contact_email=data.get("sender_contact_email", ""),
            signature=data.get("signature", ""),
            yearsinbusiness=data.get("yearsinbusiness"),
            ESG_impact_ratio=data.get("ESG_impact_ratio"),
        )

    def create_signature(self, private_key: str = "default_key") -> None:
        """Create a simple digital signature for the intent."""
        if isinstance(self.timestamp, datetime):
            ts = self.timestamp.isoformat()
        else:
            ts = str(self.timestamp)
        content = f"{self.request_id}{ts}{self.consumer.company_id}"
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
    if isinstance(signature, dict):
        return signature['algorithm'] == "SHA256" and signature['public_key'] == expected_public_key
    else:
        # It's a DigitalSignature object
        return signature.algorithm == "SHA256" and signature.public_key == expected_public_key
