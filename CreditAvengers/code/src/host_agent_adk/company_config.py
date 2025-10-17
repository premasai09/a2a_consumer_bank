import uuid
from datetime import datetime
import os
import secrets

class CorporateConfig:
    """
    Configuration class for a retail chain company.
    Represents a regional retail chain with seasonal cash flow patterns and expansion strategy.
    """
    
    def __init__(self):
        # Core identifiers
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"  # ISO8601 with Z suffix for UTC
        self.nonce = secrets.token_hex(16)  # 32-character random hex string
        self.protocol_version = "WFAP-1.0"
        
        # Company identifiers
        self.sender_id = "098765432"  # DUNS number
        self.sender_name = "Pacific Coast Home & Garden LLC"
        self.sender_public_jwk_url = "https://api.pchomeandgarden.com/keys/public.jwk"
        self.company_registration_number = "LLC-2019-4567890"  # California LLC number format
        self.jurisdiction = "US-CA"  # California, United States
        
        # Industry and tax information
        self.industry_code = "444190"  # NAICS code for Other Building Material Dealers
        self.tax_id = "77-3456789"  # EIN format
        self.ESG_impact_ratio = "0.5"  # Moderate ESG focus with sustainability initiatives
        self.carbon_emissions_tons_co2e = 8500  # Moderate emissions for retail chain (stores, transportation, facilities)
        
        # Financial data (in USD) - Retail chain with seasonal variations
        self.financials_annual_revenue = 95000000  # $95M
        self.financials_net_income = 4750000  # $4.75M (5% margin typical for retail)
        self.financials_assets_total = 78000000  # $78M (inventory heavy)
        self.financials_liabilities_total = 42000000  # $42M (including seasonal credit lines)
        
        # Credit and ESG information
        self.credit_report_ref = "DN-33445566"  # D&B reference number
        self.esg_certifications = "LEED,ENERGY STAR,FAIR TRADE"
        self.esg_reporting_url = "https://pchomeandgarden.com/sustainability-commitment"
        
        # Regulatory information
        self.regulatory_context_jurisdiction = "CPSC,FTC,California CARB"
        self.regulatory_context_required_disclosures = "California Prop 65,CPSC Product Safety Reports,FTC Truth in Advertising"
    
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