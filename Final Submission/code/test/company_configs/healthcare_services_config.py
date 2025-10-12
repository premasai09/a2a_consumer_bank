import uuid
from datetime import datetime
import os
import secrets

class CorporateConfig:
    """
    Configuration class for a healthcare services company.
    Represents a multi-location healthcare provider with stable revenue and heavy regulation compliance.
    """
    
    def __init__(self):
        # Core identifiers
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"  # ISO8601 with Z suffix for UTC
        self.nonce = secrets.token_hex(16)  # 32-character random hex string
        self.protocol_version = "WFAP-1.0"
        
        # Company identifiers
        self.sender_id = "054321098"  # DUNS number
        self.sender_name = "Sunshine Medical Group P.A."
        self.sender_public_jwk_url = "https://secure.sunshinemedical.com/keys/public.jwk"
        self.company_registration_number = "PA-987654321"  # Florida Professional Association
        self.jurisdiction = "US-FL"  # Florida, United States
        
        # Industry and tax information
        self.industry_code = "621111"  # NAICS code for Offices of Physicians (except Mental Health Specialists)
        self.tax_id = "59-1234567"  # EIN format
        self.ESG_impact_ratio = "0.8"  # High ESG focus due to healthcare mission
        self.carbon_emissions_tons_co2e = 12500  # Moderate emissions for healthcare facilities (medical equipment, HVAC, transportation)
        
        # Financial data (in USD) - Healthcare services with stable recurring revenue
        self.financials_annual_revenue = 125000000  # $125M
        self.financials_net_income = 18750000  # $18.75M (15% margin, good for healthcare)
        self.financials_assets_total = 95000000  # $95M (medical equipment and facilities)
        self.financials_liabilities_total = 35000000  # $35M
        
        # Credit and ESG information
        self.credit_report_ref = "DN-77889900"  # D&B reference number
        self.esg_certifications = "ISO26000,ENERGY STAR,LEED"
        self.esg_reporting_url = "https://sunshinemedical.com/community-health-impact"
        
        # Regulatory information
        self.regulatory_context_jurisdiction = "CMS,FDA,Florida DOH,HIPAA"
        self.regulatory_context_required_disclosures = "CMS Quality Reporting,HIPAA Risk Assessments,Florida Medical License Renewals"
    
    def to_dict(self):
        """Convert configuration to dictionary"""
        return {k: v for k, v in self.__dict__.items()}
    
    def from_dict(self, config_dict):
        """
        Update configuration from dictionary
        
        Args:
            config_dict (dict): Dictionary containing configuration values
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __str__(self):
        """String representation of configuration"""
        return f"CorporateConfig for {self.sender_name} (ID: {self.sender_id})"