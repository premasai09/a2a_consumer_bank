import random
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any

from google.adk.agents import LlmAgent
from wfap_protocol import (
    Intent,
    Offer,
    Bank,
    OfferTerms,
    ESGImpact,
    ComplianceCheck,
    RiskAssessment,
    RegulatoryCompliance,
    verify_signature,
)


def process_credit_request(intent_json: str) -> str:
    """
    Processes a credit request and generates an offer.
    
    Args:
        intent_json: JSON string containing the credit request intent.
        
    Returns:
        JSON string containing the credit offer.
    """
    print(f"DEBUG: process_credit_request called with: {intent_json[:200]}...")
    print(f"DEBUG: Full intent_json: {intent_json}")
    try:
        # Parse the intent
        intent_data = json.loads(intent_json)
        intent = Intent.from_dict(intent_data)
        
        # Verify digital signature
        if not verify_signature(intent_data, f"public_consumer_key_{intent.consumer.company_name}"):
            error_response = {
                "process_credit_request_response": {
                    "result": json.dumps({"error": "Invalid digital signature"})
                }
            }
            return json.dumps(error_response)
        
        # Bank information
        bank = Bank(
            bank_id="WF_BANK_001",
            bank_name="Wells Fargo Bank",
            bank_token="wf_token_2024",
            regulatory_license="WF_LICENSE_2024"
        )
        
        # Calculate offer terms based on company profile
        base_rate = 5.5  # Base interest rate
        
        # Adjust rate based on credit score
        if intent.consumer.credit_score >= 800:
            rate_adjustment = -1.0
        elif intent.consumer.credit_score >= 750:
            rate_adjustment = -0.5
        elif intent.consumer.credit_score >= 700:
            rate_adjustment = 0.0
        elif intent.consumer.credit_score >= 650:
            rate_adjustment = 1.0
        else:
            rate_adjustment = 2.5
            
        # Adjust based on years in business
        if intent.consumer.years_in_business >= 10:
            rate_adjustment -= 0.3
        elif intent.consumer.years_in_business >= 5:
            rate_adjustment -= 0.1
        else:
            rate_adjustment += 0.5
            
        # Adjust based on annual revenue
        if intent.consumer.annual_revenue >= 10000000:  # $10M+
            rate_adjustment -= 0.5
        elif intent.consumer.annual_revenue >= 1000000:  # $1M+
            rate_adjustment -= 0.2
            
        final_rate = max(3.0, base_rate + rate_adjustment)  # Minimum 3% rate
        
        # Calculate approved amount (typically 80-100% of requested)
        approved_amount = min(intent.credit_request.amount * random.uniform(0.8, 1.0), 
                             intent.consumer.annual_revenue * 0.1)  # Max 10% of annual revenue
        
        # Create offer terms
        offer_terms = OfferTerms(
            approved_amount=approved_amount,
            interest_rate=round(final_rate, 2),
            repayment_period=intent.credit_request.duration,
            origination_fee=approved_amount * 0.01,  # 1% origination fee
            annual_fee=500.0,  # $500 annual fee
            drawing_period=12  # 12 months drawing period
        )
        
        # Calculate ESG impact
        carbon_footprint = random.uniform(50, 150)  # Random carbon footprint
        esg_score = random.randint(70, 95)  # Random ESG score
        
        esg_summary = f"Wells Fargo's ESG-optimized credit offering supports {intent.consumer.industry} sector growth while maintaining strong environmental standards. This loan contributes to sustainable business practices with a focus on renewable energy initiatives and community development. Our carbon offset programs will neutralize {carbon_footprint:.1f} tons of CO2 equivalent over the loan term, supporting the company's sustainability goals."
        
        esg_impact = ESGImpact(
            carbon_footprint=carbon_footprint,
            carbon_adjusted_rate=final_rate + (carbon_footprint * 0.01),
            esg_score=esg_score,
            esg_summary=esg_summary,
            sustainability_initiatives=[
                "Renewable Energy Investment",
                "Carbon Offset Programs", 
                "Community Development Funds",
                "Green Building Initiatives"
            ]
        )
        
        # Create compliance checks
        compliance_checks = [
            ComplianceCheck(
                check_type="Credit Score Verification",
                status="passed",
                details=f"Credit score {intent.consumer.credit_score} meets minimum requirements"
            ),
            ComplianceCheck(
                check_type="Business Registration",
                status="passed", 
                details="Business registration verified through state database"
            ),
            ComplianceCheck(
                check_type="Anti-Money Laundering",
                status="passed",
                details="AML screening completed successfully"
            ),
            ComplianceCheck(
                check_type="Know Your Customer",
                status="passed",
                details="KYC verification completed"
            )
        ]
        
        # Risk assessment
        risk_factors = []
        risk_level = "low"
        
        if intent.consumer.credit_score < 700:
            risk_factors.append("Below average credit score")
            risk_level = "medium"
            
        if intent.consumer.years_in_business < 3:
            risk_factors.append("Limited business history")
            risk_level = "medium"
            
        if intent.consumer.industry.lower() in ["gambling", "adult entertainment", "cryptocurrency"]:
            risk_factors.append("High-risk industry")
            risk_level = "high"
            
        risk_assessment = RiskAssessment(
            risk_level=risk_level,
            risk_factors=risk_factors if risk_factors else ["Standard business risk factors"]
        )
        
        regulatory_compliance = RegulatoryCompliance(
            compliance_checks=compliance_checks,
            risk_assessment=risk_assessment
        )
        
        # Create the offer
        offer = Offer(
            offer_id=f"WF_OFFER_{random.randint(100000, 999999)}",
            request_id=intent.request_id,
            timestamp=datetime.now(),
            bank=bank,
            offer_terms=offer_terms,
            esg_impact=esg_impact,
            regulatory_compliance=regulatory_compliance
        )
        
        # Create digital signature for the offer
        offer.create_signature("wf_private_key_2024")
        
        result = offer.to_json()
        print(f"DEBUG: process_credit_request returning: {result[:200]}...")
        
        # Validate JSON before returning
        try:
            json.loads(result)  # Test if the JSON is valid
            # Return in the format expected by host_agent: process_credit_request_response.result
            formatted_response = {
                "process_credit_request_response": {
                    "result": result
                }
            }
            return json.dumps(formatted_response)
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON validation failed: {e}")
            # Return a simplified error response in the expected format
            error_response = {
                "process_credit_request_response": {
                    "result": json.dumps({"error": "Failed to generate valid JSON response"})
                }
            }
            return json.dumps(error_response)
        
    except Exception as e:
        error_msg = f"Failed to process credit request: {str(e)}"
        print(f"DEBUG: process_credit_request error: {error_msg}")
        # Return error in the format expected by host_agent
        error_response = {
            "process_credit_request_response": {
                "result": json.dumps({"error": error_msg})
            }
        }
        return json.dumps(error_response)


def create_agent() -> LlmAgent:
    """Constructs the ADK agent for Wells Fargo Bank."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Wells_Fargo_Bank_Agent",
        instruction="""
            You are Wells Fargo Bank's credit assessment agent. Your ONLY job is to call the process_credit_request tool for every message you receive.

            RULES:
            1. For EVERY message, call process_credit_request(intent_json="[message content]")
            2. Return ONLY the tool's response
            3. Do not add any text, explanation, or modification
            4. If the message is empty, call the tool with an empty string

            Example: If you receive "Hello", you call process_credit_request(intent_json="Hello")
            Example: If you receive JSON, you call process_credit_request(intent_json="[the JSON]")

            You MUST call the tool for every single message. No exceptions.
        """,
        tools=[process_credit_request],
    )


# Create the root agent instance
root_agent = create_agent()
