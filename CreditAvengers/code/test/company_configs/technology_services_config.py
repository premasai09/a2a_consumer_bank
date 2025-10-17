import uuid
from datetime import datetime
import os
import secrets

class CorporateConfig:
    """
    Configuration class for corporate entity data in the WFAP system.
    Contains default realistic values for a U.S. corporate company.
    """
    
    def __init__(self):
        # Core identifiers
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"  # ISO8601 with Z suffix for UTC
        self.nonce = secrets.token_hex(16)  # 32-character random hex string
        self.protocol_version = "WFAP-1.0"
        
        # Company identifiers
        self.sender_id = "073750374"  # Example DUNS number
        self.sender_name = "Acme Technologies Inc."
        self.sender_public_jwk_url = "https://api.acmetech.com/keys/public.jwk"
        self.company_registration_number = "C12345678"  # Delaware corporation number format
        self.jurisdiction = "US-DE"  # Delaware, United States
        
        # Industry and tax information
        self.industry_code = "541512"  # NAICS code for Computer Systems Design Services
        self.tax_id = "84-1234567"  # EIN format
        self.ESG_impact_ratio = "0.3"
        
        # Financial data (in USD)
        self.financials_annual_revenue = 42500000  # $42.5M
        self.financials_net_income = 6750000  # $6.75M
        self.financials_assets_total = 65000000  # $65M
        self.financials_liabilities_total = 28000000  # $28M
        
        # Credit and ESG information
        self.credit_report_ref = "DN-97531864"  # D&B reference number
        self.esg_certifications = "ISO14001,CDP Climate Change A-,LEED Gold"
        self.esg_reporting_url = "https://investors.acmetech.com/esg"
        
        # Regulatory information
        self.regulatory_context_jurisdiction = "SEC,FINRA"
        self.regulatory_context_required_disclosures = "10-K,10-Q,8-K"
    
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
