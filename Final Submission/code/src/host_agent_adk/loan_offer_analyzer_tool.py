import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class LoanOfferAnalyzer:
    """
    Agent tool for analyzing loan offers and selecting the best one
    based on loan request criteria and offer terms
    """
    
    def __init__(self):
        self.weight_config = {
            "interest_rate": 0.4,      # 40% weight - most important
            "amount_approved": 0.25,    # 25% weight - getting full amount
            "repayment_match": 0.15,    # 15% weight - matching preferences
            "esg_compliance": 0.1,      # 10% weight - ESG considerations
            "offer_recency": 0.1        # 10% weight - newer offers preferred
        }
    
    def analyze_loan_offers(self, loan_request: Dict[str, Any], bank_offers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main function to analyze loan offers and return the best offer
        
        Args:
            loan_request: Dictionary containing loan request details
            bank_offers: List of dictionaries containing bank offer details
            
        Returns:
            Dictionary with best offer details including bank_id
        """
        if not bank_offers:
            return {"error": "No bank offers provided", "bankid": None}
        
        if not loan_request:
            return {"error": "No loan request provided", "bankid": None}
        
        # Score each offer
        scored_offers = []
        for offer in bank_offers:
            score = self._calculate_offer_score(loan_request, offer)
            scored_offers.append({
                "offer": offer,
                "score": score,
                "bank_id": offer.get("bankid", "unknown")
            })
        
        # Sort by score (highest first)
        scored_offers.sort(key=lambda x: x["score"], reverse=True)
        
        best_offer = scored_offers[0]
        
        return {
            "bankid": best_offer["bank_id"],
            "best_offer_details": best_offer["offer"],
            "total_score": best_offer["score"],
            "analysis_summary": self._generate_analysis_summary(loan_request, best_offer["offer"]),
            "all_scores": [(offer["bank_id"], offer["score"]) for offer in scored_offers]
        }
    
    def _calculate_offer_score(self, loan_request: Dict[str, Any], offer: Dict[str, Any]) -> float:
        """
        Calculate a composite score for a loan offer based on multiple criteria
        """
        score = 0.0
        
        # 1. Interest Rate Score (lower is better)
        score += self._score_interest_rate(loan_request, offer) * self.weight_config["interest_rate"]
        
        # 2. Amount Approved Score (closer to requested amount is better)
        score += self._score_amount_approved(loan_request, offer) * self.weight_config["amount_approved"]
        
        # 3. Repayment Terms Match Score
        score += self._score_repayment_match(loan_request, offer) * self.weight_config["repayment_match"]
        
        # 4. ESG Compliance Score
        score += self._score_esg_compliance(loan_request, offer) * self.weight_config["esg_compliance"]
        
        # 5. Offer Recency Score
        score += self._score_offer_recency(offer) * self.weight_config["offer_recency"]
        
        return round(score, 2)
    
    def _score_interest_rate(self, loan_request: Dict[str, Any], offer: Dict[str, Any]) -> float:
        """Score based on interest rate comparison"""
        preferred_rate = loan_request.get("preferred_interest_rate", 0)
        offered_rate = offer.get("interest_rate_annual", float('inf'))
        
        if preferred_rate == 0:
            # If no preference, lower rates get higher scores
            return max(0, (15 - offered_rate) / 15 * 100)
        
        # Score based on how close to preferred rate (lower is better)
        rate_diff = abs(offered_rate - preferred_rate)
        if offered_rate <= preferred_rate:
            return 100  # Perfect or better than expected
        else:
            # Penalty for rates higher than preferred
            penalty = min(rate_diff * 10, 100)
            return max(0, 100 - penalty)
    
    def _score_amount_approved(self, loan_request: Dict[str, Any], offer: Dict[str, Any]) -> float:
        """Score based on approved amount vs requested amount"""
        requested_amount = loan_request.get("amount_value", 0)
        approved_amount = offer.get("amount_approved", 0)
        
        if requested_amount == 0 or approved_amount == 0:
            return 0
        
        ratio = approved_amount / requested_amount
        if ratio >= 1.0:
            return 100  # Full amount or more approved
        else:
            return ratio * 100  # Proportional score
    
    def _score_repayment_match(self, loan_request: Dict[str, Any], offer: Dict[str, Any]) -> float:
        """Score based on repayment terms matching preferences"""
        score = 0
        
        # Duration match
        requested_duration = loan_request.get("repayment_duration", 0)
        offered_duration = offer.get("repayment_duration_months", 0)
        
        if requested_duration > 0 and offered_duration > 0:
            duration_diff = abs(offered_duration - requested_duration)
            duration_score = max(0, 100 - (duration_diff * 2))  # 2 points penalty per month difference
            score += duration_score * 0.6
        
        # Repayment type match
        requested_type = loan_request.get("repayment_preference", "").lower()
        offered_type = offer.get("repayment_schedule", "").lower()
        
        if requested_type and offered_type:
            if requested_type == offered_type:
                score += 40  # 40 points for exact match
            else:
                score += 20  # 20 points for any repayment schedule
        
        return min(score, 100)
    
    def _score_esg_compliance(self, loan_request: Dict[str, Any], offer: Dict[str, Any]) -> float:
        """Score based on ESG compliance and reporting"""
        score = 50  # Base score
        
        # Check if ESG reporting was requested
        esg_url_requested = loan_request.get("esg_reporting_url", "")
        esg_summary = offer.get("esg_impact_summary", "")
        
        if esg_url_requested or esg_summary:
            if esg_summary and len(esg_summary.strip()) > 0:
                score += 50  # Bonus for providing ESG information
        
        return min(score, 100)
    
    def _score_offer_recency(self, offer: Dict[str, Any]) -> float:
        """Score based on how recent the offer is"""
        created_date_str = offer.get("created_date", "")
        
        if not created_date_str:
            return 50  # Default score if no date provided
        
        try:
            # Parse the date format: 2025-8-20-16:7-932
            date_parts = created_date_str.replace("-", ":").split(":")
            if len(date_parts) >= 5:
                year, month, day, hour, minute = map(int, date_parts[:5])
                offer_date = datetime(year, month, day, hour, minute)
                current_date = datetime.now()
                
                days_old = (current_date - offer_date).days
                
                # Newer offers get higher scores
                if days_old <= 1:
                    return 100
                elif days_old <= 7:
                    return 80
                elif days_old <= 30:
                    return 60
                else:
                    return 40
        except:
            pass
        
        return 50  # Default score if date parsing fails
    
    def _generate_analysis_summary(self, loan_request: Dict[str, Any], best_offer: Dict[str, Any]) -> str:
        """Generate a human-readable summary of why this offer was selected"""
        summary_parts = []
        
        # Interest rate comparison
        preferred_rate = loan_request.get("preferred_interest_rate", 0)
        offered_rate = best_offer.get("interest_rate_annual", 0)
        
        if preferred_rate > 0:
            if offered_rate <= preferred_rate:
                summary_parts.append(f"Interest rate of {offered_rate}% meets or beats preferred rate of {preferred_rate}%")
            else:
                summary_parts.append(f"Interest rate of {offered_rate}% is {offered_rate - preferred_rate:.2f}% above preferred rate")
        else:
            summary_parts.append(f"Competitive interest rate of {offered_rate}%")
        
        # Amount comparison
        requested_amount = loan_request.get("amount_value", 0)
        approved_amount = best_offer.get("amount_approved", 0)
        
        if approved_amount >= requested_amount:
            summary_parts.append(f"Full requested amount of ${approved_amount:,.0f} approved")
        else:
            percentage = (approved_amount / requested_amount) * 100
            summary_parts.append(f"{percentage:.1f}% of requested amount approved (${approved_amount:,.0f})")
        
        # Repayment terms
        offered_duration = best_offer.get("repayment_duration_months", 0)
        if offered_duration > 0:
            summary_parts.append(f"{offered_duration} months repayment term")
        
        return "; ".join(summary_parts)


# Google ADK Agent Function Definitions
def select_best_loan_offer(loan_request_json: str, bank_offers_json: str) -> str:
    """
    Google ADK compatible function to select the best loan offer
    
    Args:
        loan_request_json: JSON string containing loan request details
        bank_offers_json: JSON string containing list of bank offers
        
    Returns:
        JSON string with analysis results including best bank_id
    """
    try:
        loan_request = json.loads(loan_request_json)
        bank_offers = json.loads(bank_offers_json)
        
        analyzer = LoanOfferAnalyzer()
        result = analyzer.analyze_loan_offers(loan_request, bank_offers)
        
        return json.dumps(result, indent=2)
    
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON input: {str(e)}", "bankid": None})
    except Exception as e:
        return json.dumps({"error": f"Analysis failed: {str(e)}", "bankid": None})


def get_bankid_only(loan_request_json: str, bank_offers_json: str) -> str:
    """
    Simplified function that returns only the best bank ID
    
    Args:
        loan_request_json: JSON string containing loan request details
        bank_offers_json: JSON string containing list of bank offers
        
    Returns:
        String containing the best bank ID or error message
    """
    try:
        result_json = select_best_loan_offer(loan_request_json, bank_offers_json)
        result = json.loads(result_json)
        
        if result.get("error"):
            return f"ERROR: {result['error']}"
        
        return result.get("bankid", "No bank ID found")
    
    except Exception as e:
        return f"ERROR: {str(e)}"
