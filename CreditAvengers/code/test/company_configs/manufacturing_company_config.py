import uuid
from datetime import datetime
import os
import secrets

class CorporateConfig:
    """
    Configuration class for an established manufacturing company.
    Represents a conservative, asset-heavy industrial manufacturer with steady operations.
    """
    
    def __init__(self):
        # Core identifiers
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"  # ISO8601 with Z suffix for UTC
        self.nonce = secrets.token_hex(16)  # 32-character random hex string
        self.protocol_version = "WFAP-1.0"
        
        # Company identifiers
        self.sender_id = "019876543"  # DUNS number
        self.sender_name = "Midwest Steel Manufacturing Corp."
        self.sender_public_jwk_url = "https://portal.midweststeel.com/keys/public.jwk"
        self.company_registration_number = "C19876543"  # Ohio corporation number format
        self.jurisdiction = "US-OH"  # Ohio, United States
        
        # Industry and tax information
        self.industry_code = "331110"  # NAICS code for Iron and Steel Mills and Ferroalloy Manufacturing
        self.tax_id = "34-5678901"  # EIN format
        self.ESG_impact_ratio = "0.4"  # Moderate ESG focus, improving sustainability
        self.carbon_emissions_tons_co2e = 285000  # High emissions for steel manufacturing (energy-intensive processes)
        
        # Financial data (in USD) - Established manufacturing with strong assets
        self.financials_annual_revenue = 185000000  # $185M
        self.financials_net_income = 14800000  # $14.8M (8% margin)
        self.financials_assets_total = 320000000  # $320M (heavy in plant & equipment)
        self.financials_liabilities_total = 125000000  # $125M
        
        # Credit and ESG information
        self.credit_report_ref = "DN-55667788"  # D&B reference number
        self.esg_certifications = "ISO14001,ENERGY STAR,SA8000"
        self.esg_reporting_url = "https://midweststeel.com/environmental-stewardship"
        
        # Regulatory information
        self.regulatory_context_jurisdiction = "EPA,OSHA,DOT"
        self.regulatory_context_required_disclosures = "EPA Toxic Release Inventory,OSHA 300 Logs,DOT Hazmat Reports"
    
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