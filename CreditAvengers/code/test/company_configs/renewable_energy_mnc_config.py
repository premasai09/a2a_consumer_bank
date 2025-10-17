
import uuid
from datetime import datetime
import os
import secrets

class CorporateConfig:
    """
    Configuration class for a renewable energy multinational corporation.
    Represents a large ESG-focused energy company with capital-intensive operations.
    """
    
    def __init__(self):
        # Core identifiers
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"  # ISO8601 with Z suffix for UTC
        self.nonce = secrets.token_hex(16)  # 32-character random hex string
        self.protocol_version = "WFAP-1.0"
        
        # Company identifiers
        self.sender_id = "012345678"  # DUNS number
        self.sender_name = "GreenPower Global Corporation"
        self.sender_public_jwk_url = "https://investor.greenpowerglobal.com/keys/public.jwk"
        self.company_registration_number = "C01234567"  # Delaware corporation number format
        self.jurisdiction = "US-DE"  # Delaware, United States (but global operations)
        
        # Industry and tax information
        self.industry_code = "221114"  # NAICS code for Solar Electric Power Generation
        self.tax_id = "12-3456789"  # EIN format
        self.ESG_impact_ratio = "0.95"  # Extremely high ESG focus - core business model
        self.carbon_emissions_tons_co2e = 2800  # Very low emissions for renewable energy company (construction, maintenance only)
        
        # Financial data (in USD) - Large MNC with significant capital investments
        self.financials_annual_revenue = 850000000  # $850M
        self.financials_net_income = 127500000  # $127.5M (15% margin)
        self.financials_assets_total = 2400000000  # $2.4B (massive infrastructure assets)
        self.financials_liabilities_total = 980000000  # $980M (project financing)
        
        # Credit and ESG information
        self.credit_report_ref = "DN-99887766"  # D&B reference number
        self.esg_certifications = "CDP,SBTI,UN GLOBAL COMPACT,GRI,TCFD,B-CORP,CARBON NEUTRAL"
        self.esg_reporting_url = "https://greenpowerglobal.com/esg-impact-report"
        
        # Regulatory information
        self.regulatory_context_jurisdiction = "SEC,FERC,EPA,NERC,IRS Section 45"
        self.regulatory_context_required_disclosures = "10-K,10-Q,8-K,FERC Form 1,EPA eGRID,Production Tax Credit Filings"
    
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