import uuid
from datetime import datetime
import os
import secrets

class CorporateConfig:
    """
    Configuration class for a high-growth tech startup (Series B).
    Represents a fast-growing SaaS company with aggressive expansion strategy.
    """
    
    def __init__(self):
        # Core identifiers
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"  # ISO8601 with Z suffix for UTC
        self.nonce = secrets.token_hex(16)  # 32-character random hex string
        self.protocol_version = "WFAP-1.0"
        
        # Company identifiers
        self.sender_id = "087654321"  # DUNS number
        self.sender_name = "CloudScale AI Inc."
        self.sender_public_jwk_url = "https://api.cloudscaleai.com/keys/public.jwk"
        self.company_registration_number = "C87654321"  # Delaware corporation number format
        self.jurisdiction = "US-DE"  # Delaware, United States
        
        # Industry and tax information
        self.industry_code = "541511"  # NAICS code for Custom Computer Programming Services
        self.tax_id = "85-9876543"  # EIN format
        self.ESG_impact_ratio = "0.7"  # High ESG focus for modern startup
        self.carbon_emissions_tons_co2e = 450  # Low emissions for tech startup (office operations, cloud services)
        
        # Financial data (in USD) - Series B startup with rapid growth
        self.financials_annual_revenue = 15000000  # $15M ARR
        self.financials_net_income = -2500000  # Negative (growth investment phase)
        self.financials_assets_total = 25000000  # $25M (including cash from funding)
        self.financials_liabilities_total = 8000000  # $8M
        
        # Credit and ESG information
        self.credit_report_ref = "DN-11223344"  # D&B reference number
        self.esg_certifications = "B-CORP,CARBON NEUTRAL,ISO14001"
        self.esg_reporting_url = "https://cloudscaleai.com/sustainability"
        
        # Regulatory information
        self.regulatory_context_jurisdiction = "SEC,SOX"
        self.regulatory_context_required_disclosures = "409A Valuations,Delaware Annual Report"
    
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