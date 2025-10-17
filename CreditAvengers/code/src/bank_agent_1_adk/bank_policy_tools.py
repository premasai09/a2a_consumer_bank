import json
import sys
import os
import requests
import re
from .wfap_protocol import BANK_POLICIES
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from typing import Dict, Any, List

def fetch_carbon_emissions_from_esg_report(esg_reporting_url: str) -> float:
    """
    Fetch carbon emissions data from ESG report URL.
    
    Args:
        esg_reporting_url: URL to the ESG report (e.g., GitHub Gist)
    
    Returns:
        Carbon emissions value in tons CO2e
    """
    
    if not esg_reporting_url or esg_reporting_url.lower() in ["", "none", "null"]:
        return 0.0  # Default to 0 if no URL provided
    
    try:
        # Fetch the ESG report content
        response = requests.get(esg_reporting_url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        
        # Parse carbon emissions from the content
        # Look for patterns like "Carbon Emissions = 450" or "Carbon Emissions: 450"
        patterns = [
            r'Carbon\s+Emissions\s*[=:]\s*(\d+(?:\.\d+)?)',
            r'carbon\s+emissions\s*[=:]\s*(\d+(?:\.\d+)?)',
            r'Total\s+Emissions\s*[=:]\s*(\d+(?:\.\d+)?)',
            r'total\s+emissions\s*[=:]\s*(\d+(?:\.\d+)?)',
            r'CO2\s+Emissions\s*[=:]\s*(\d+(?:\.\d+)?)',
            r'co2\s+emissions\s*[=:]\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                emissions_value = float(match.group(1))
                return emissions_value
        
        # If no pattern matches, try to find any number that might be emissions
        # This is a fallback - look for standalone numbers
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', content)
        if numbers:
            # Take the first number found as a fallback
            return float(numbers[0])
        
        # If nothing found, return 0
        return 0.0
        
    except requests.RequestException as e:
        print(f"Warning: Failed to fetch ESG report from {esg_reporting_url}: {str(e)}")
        return 0.0  # Return 0 if URL fetch fails
    except ValueError as e:
        print(f"Warning: Failed to parse carbon emissions from ESG report: {str(e)}")
        return 0.0
    except Exception as e:
        print(f"Warning: Unexpected error fetching ESG report: {str(e)}")
        return 0.0


def perform_initial_risk_assessment(
    intent_id: str,
    sender_name: str,
    amount_value: float,
    jurisdiction: str,
    industry_code: str,
    financials_annual_revenue: float,
    financials_net_income: float,
    financials_assets_total: float,
    financials_liabilities_total: float
) -> Dict[str, Any]:
    """
    Performs initial risk assessment for corporate line of credit application.
    
    Returns:
        Dictionary with assessment result (PASS/FAIL) and detailed reasons
    """
    
    assessment_results = []
    overall_status = "PASS"
    
    try:
        # 1. INDUSTRY ELIGIBILITY CHECK
        industry_status = check_industry_eligibility(industry_code)
        assessment_results.append(industry_status)
        if industry_status["status"] == "FAIL":
            overall_status = "FAIL"
            print("1 -Fail")
        
        # 2. LOAN AMOUNT LIMITS CHECK
        amount_status = check_loan_amount_limits(amount_value)
        assessment_results.append(amount_status)
        if amount_status["status"] == "FAIL":
            overall_status = "FAIL"
            print("2 -Fail")
        
        # 3. GEOGRAPHIC/JURISDICTION CHECK
        jurisdiction_status = check_jurisdiction_eligibility(jurisdiction)
        assessment_results.append(jurisdiction_status)
        if jurisdiction_status["status"] == "FAIL":
            overall_status = "FAIL"
            print("3 -Fail")
        
        # 4. MINIMUM REVENUE CHECK
        revenue_status = check_minimum_revenue(financials_annual_revenue)
        assessment_results.append(revenue_status)
        if revenue_status["status"] == "FAIL":
            overall_status = "FAIL"
            print("4 -Fail")
        
        # 5. DEBT-TO-ASSET RATIO CHECK
        debt_ratio_status = check_debt_to_asset_ratio(
            financials_liabilities_total, 
            financials_assets_total
        )
        assessment_results.append(debt_ratio_status)
        if debt_ratio_status["status"] == "FAIL":
            overall_status = "FAIL"
            print("5 -Fail")
        
        # 6. BASIC FINANCIAL HEALTH CHECKS
        financial_health_status = check_basic_financial_health(
            financials_annual_revenue,
            financials_net_income,
            financials_assets_total,
            financials_liabilities_total
        )
        assessment_results.append(financial_health_status)
        if financial_health_status["status"] == "FAIL":
            overall_status = "FAIL"
            print("6 -Fail")
        
        # Compile final assessment
        passed_checks = len([r for r in assessment_results if r["status"] == "PASS"])
        total_checks = len(assessment_results)
        
        return {
            "overall_status": overall_status,
            "intent_id": intent_id,
            "sender_name": sender_name,
            "assessment_summary": f"Passed {passed_checks}/{total_checks} initial risk checks",
            "detailed_results": assessment_results,
            "next_steps": "Proceed to detailed underwriting" if overall_status == "PASS" else "Application rejected - does not meet basic eligibility criteria"
        }
        
    except Exception as e:
        return {
            "overall_status": "ERROR",
            "error": f"Risk assessment failed: {str(e)}",
            "intent_id": intent_id,
            "sender_name": sender_name
        }


def check_industry_eligibility(industry_code: str) -> Dict[str, Any]:
    """Check if the industry is eligible for lending"""
    
    # Map industry codes to our internal risk classifications
    industry_mapping = {
        "621": "healthcare_services",  # Healthcare
        "221": "utilities",           # Utilities
        "311": "food_processing",     # Food Manufacturing
        "541": "professional_services", # Professional Services
        "518": "technology_software",  # Software
        "336": "manufacturing",       # Manufacturing
        "441": "retail_trade",        # Retail
        "484": "transportation",      # Transportation
        "236": "construction",        # Construction
        "423": "wholesale_trade",     # Wholesale
        "211": "oil_gas",            # Oil & Gas
        "212": "mining",             # Mining
        "111": "agriculture",        # Agriculture
        "721": "hospitality",        # Hospitality
        "531": "real_estate",        # Real Estate
        "522": "cryptocurrency",     # Crypto/Fintech
        "713": "gambling",           # Gambling
        "812": "adult_entertainment", # Adult Entertainment
        "111998": "cannabis"         # Cannabis
    }
    
    # Get first 3 digits of NAICS code for broad industry classification
    industry_key = industry_code[:3] if len(industry_code) >= 3 else industry_code
    mapped_industry = industry_mapping.get(industry_key, "unknown")
    
    # Check if industry is prohibited
    if mapped_industry in BANK_POLICIES.prohibited_industries:
        return {
            "check": "Industry Eligibility",
            "status": "FAIL",
            "reason": f"Industry '{mapped_industry}' is on prohibited list",
            "industry_code": industry_code,
            "risk_level": "PROHIBITED"
        }
    
    # Check industry risk level
    if mapped_industry in BANK_POLICIES.industry_risk_levels:
        risk_level = BANK_POLICIES.industry_risk_levels[mapped_industry]
        return {
            "check": "Industry Eligibility", 
            "status": "PASS",
            "reason": f"Industry '{mapped_industry}' is acceptable",
            "industry_code": industry_code,
            "risk_level": risk_level.value
        }
    
    # Unknown industry - treat as medium risk but flag for manual review
    return {
        "check": "Industry Eligibility",
        "status": "PASS",
        "reason": f"Unknown industry code '{industry_code}' - requires manual review",
        "industry_code": industry_code,
        "risk_level": "MEDIUM",
        "manual_review_required": True
    }


def check_loan_amount_limits(amount_value: float) -> Dict[str, Any]:
    """Check if loan amount is within acceptable limits"""
    
    if amount_value < BANK_POLICIES.min_credit_limit:
        return {
            "check": "Loan Amount Limits",
            "status": "FAIL", 
            "reason": f"Requested amount ${amount_value:,.2f} is below minimum ${BANK_POLICIES.min_credit_limit:,.2f}",
            "requested_amount": amount_value,
            "min_limit": BANK_POLICIES.min_credit_limit
        }
    
    if amount_value > BANK_POLICIES.max_credit_limit_absolute:
        return {
            "check": "Loan Amount Limits",
            "status": "FAIL",
            "reason": f"Requested amount ${amount_value:,.2f} exceeds maximum ${BANK_POLICIES.max_credit_limit_absolute:,.2f}",
            "requested_amount": amount_value,
            "max_limit": BANK_POLICIES.max_credit_limit_absolute
        }
    
    return {
        "check": "Loan Amount Limits",
        "status": "PASS",
        "reason": f"Requested amount ${amount_value:,.2f} is within acceptable limits",
        "requested_amount": amount_value,
        "min_limit": BANK_POLICIES.min_credit_limit,
        "max_limit": BANK_POLICIES.max_credit_limit_absolute
    }


def check_jurisdiction_eligibility(jurisdiction: str) -> Dict[str, Any]:
    """Check if jurisdiction is acceptable for lending"""
    
    # Acceptable jurisdictions for corporate lending
    acceptable_jurisdictions = [
        "US", "USA", "United States",
        "CA", "Canada", 
        "UK", "United Kingdom",
        "DE", "Germany",
        "FR", "France",
        "AU", "Australia",
        "JP", "Japan"
    ]
    
    # High-risk jurisdictions
    high_risk_jurisdictions = [
        "AF", "BY", "CF", "CU", "ER", "HK", "IR", "IQ", "KP", "LB", "LY", "MM", "NI", "RU", "SO", "SS", "SD", "SY", "VE", "YE", "ZW"
    ]
    
    jurisdiction_upper = jurisdiction.upper()
    
    if jurisdiction_upper in high_risk_jurisdictions:
        return {
            "check": "Jurisdiction Eligibility",
            "status": "FAIL",
            "reason": f"Jurisdiction '{jurisdiction}' is on high-risk/sanctions list",
            "jurisdiction": jurisdiction
        }
    
    if jurisdiction_upper in acceptable_jurisdictions:
        return {
            "check": "Jurisdiction Eligibility",
            "status": "PASS", 
            "reason": f"Jurisdiction '{jurisdiction}' is acceptable",
            "jurisdiction": jurisdiction
        }
    
    return {
        "check": "Jurisdiction Eligibility",
        "status": "PASS",
        "reason": f"Jurisdiction '{jurisdiction}' requires additional due diligence",
        "jurisdiction": jurisdiction,
        "manual_review_required": True
    }


def check_minimum_revenue(annual_revenue: float) -> Dict[str, Any]:
    """Check if company meets minimum revenue requirements"""
    
    if annual_revenue < BANK_POLICIES.min_annual_revenue:
        return {
            "check": "Minimum Revenue Requirement",
            "status": "FAIL",
            "reason": f"Annual revenue ${annual_revenue:,.2f} is below minimum ${BANK_POLICIES.min_annual_revenue:,.2f}",
            "annual_revenue": annual_revenue,
            "minimum_required": BANK_POLICIES.min_annual_revenue
        }
    
    return {
        "check": "Minimum Revenue Requirement", 
        "status": "PASS",
        "reason": f"Annual revenue ${annual_revenue:,.2f} meets minimum requirement",
        "annual_revenue": annual_revenue,
        "minimum_required": BANK_POLICIES.min_annual_revenue
    }


def check_debt_to_asset_ratio(total_liabilities: float, total_assets: float) -> Dict[str, Any]:
    """Check debt-to-asset ratio"""
    
    if total_assets <= 0:
        return {
            "check": "Debt-to-Asset Ratio",
            "status": "FAIL",
            "reason": "Total assets must be greater than zero",
            "total_assets": total_assets,
            "total_liabilities": total_liabilities
        }
    
    debt_to_asset_ratio = total_liabilities / total_assets
    max_acceptable_ratio = 0.8  # 80% maximum debt-to-asset ratio
    
    if debt_to_asset_ratio > max_acceptable_ratio:
        return {
            "check": "Debt-to-Asset Ratio",
            "status": "FAIL", 
            "reason": f"Debt-to-asset ratio {debt_to_asset_ratio:.2%} exceeds maximum {max_acceptable_ratio:.2%}",
            "debt_to_asset_ratio": debt_to_asset_ratio,
            "max_acceptable_ratio": max_acceptable_ratio,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities
        }
    
    return {
        "check": "Debt-to-Asset Ratio",
        "status": "PASS",
        "reason": f"Debt-to-asset ratio {debt_to_asset_ratio:.2%} is acceptable",
        "debt_to_asset_ratio": debt_to_asset_ratio,
        "max_acceptable_ratio": max_acceptable_ratio,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities
    }


def check_basic_financial_health(annual_revenue: float, net_income: float, 
                               total_assets: float, total_liabilities: float) -> Dict[str, Any]:
    """Perform basic financial health checks"""
    
    issues = []
    
    # Check profitability
    if net_income <= 0:
        issues.append(f"Company is not profitable (Net Income: ${net_income:,.2f})")
    
    # Check if annual revenue is positive
    if annual_revenue <= 0:
        issues.append("Annual revenue must be positive")
    
    # Check asset utilization
    if total_assets > 0:
        asset_turnover = annual_revenue / total_assets
        if asset_turnover < 0.5:  # Low asset utilization
            issues.append(f"Low asset utilization ratio: {asset_turnover:.2f}")
    
    # Check equity position
    equity = total_assets - total_liabilities
    if equity <= 0:
        issues.append("Company has negative equity (insolvent)")
    
    if issues:
        return {
            "check": "Basic Financial Health",
            "status": "FAIL",
            "reason": "Multiple financial health concerns identified",
            "issues": issues,
            "annual_revenue": annual_revenue,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "equity": equity if 'equity' in locals() else None
        }
    
    return {
        "check": "Basic Financial Health",
        "status": "PASS", 
        "reason": "Basic financial health metrics are acceptable",
        "annual_revenue": annual_revenue,
        "net_income": net_income,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "equity": total_assets - total_liabilities
    }


def calculate_interest_rate_and_offer(
    intent_id: str,
    sender_name: str,
    amount_value: float,
    repayment_duration: int,
    industry_code: str,
    financials_annual_revenue: float,
    financials_net_income: float,
    financials_assets_total: float,
    financials_liabilities_total: float,
    esg_certifications: str,
    collateral_description: str,
    esg_reporting_url: str,
    carbon_emissions: float
) -> Dict[str, Any]:
    """
    Calculates interest rate and generates loan offer using weighted risk model.
    Only called if initial risk assessment passes.
    
    Returns:
        Dictionary with final interest rate, risk breakdown, and loan offer details
    """
    
    try:
        # Step 1: Fetch carbon emissions from ESG report URL
        carbon_emissions = carbon_emissions
        
        # Step 2: Calculate key financial metrics
        metrics = calculate_financial_metrics(
            financials_annual_revenue,
            financials_net_income,
            financials_assets_total,
            financials_liabilities_total
        )
        
        # Step 3: Score each metric (1-5 scale)
        scores = calculate_risk_scores(metrics)
        
        # Step 4: Calculate weighted risk score
        weighted_score = calculate_weighted_risk_score(scores)
        
        # Step 5: Determine risk premium based on score
        risk_premium = get_risk_premium_from_score(weighted_score)
        
        # Step 6: Calculate ESG discount using carbon-adjusted model
        esg_discount, esg_details = calculate_comprehensive_esg_discount(
            industry_code=industry_code,
            annual_revenue=financials_annual_revenue,
            carbon_emissions=carbon_emissions,
            esg_certifications=esg_certifications,
            esg_reporting_url=esg_reporting_url
        )
        
        # Step 7: Calculate final interest rate
        base_rate = BANK_POLICIES.base_interest_rate
        final_interest_rate = base_rate + risk_premium - esg_discount
        
        # Step 8: Generate comprehensive loan offer
        loan_offer = generate_loan_offer(
            intent_id=intent_id,
            sender_name=sender_name,
            amount_value=amount_value,
            repayment_duration=repayment_duration,
            final_interest_rate=final_interest_rate,
            risk_premium=risk_premium,
            esg_discount=esg_discount,
            weighted_score=weighted_score,
            metrics=metrics,
            scores=scores,
            collateral_description=collateral_description,
            esg_details=esg_details
        )
        
        return loan_offer
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": f"Interest rate calculation failed: {str(e)}",
            "intent_id": intent_id,
            "sender_name": sender_name
        }


def calculate_financial_metrics(annual_revenue: float, net_income: float, 
                              total_assets: float, total_liabilities: float) -> Dict[str, float]:
    """Calculate key financial metrics for risk assessment"""
    
    # Profitability Margin
    profitability_margin = (net_income / annual_revenue) if annual_revenue > 0 else -1.0
    
    # Leverage (Debt-to-Asset Ratio)  
    leverage_ratio = (total_liabilities / total_assets) if total_assets > 0 else 1.0
    
    # Company Scale (Annual Revenue)
    company_scale = annual_revenue
    
    return {
        "profitability_margin": profitability_margin,
        "leverage_ratio": leverage_ratio,
        "company_scale": company_scale
    }


def calculate_risk_scores(metrics: Dict[str, float]) -> Dict[str, float]:
    """Score each financial metric on 1-5 scale (5 = lowest risk)"""
    
    scores = {}
    
    # Profitability Margin Scoring
    profitability = metrics["profitability_margin"]
    if profitability > 0.20:  # > 20%
        scores["profitability_score"] = 5.0
    elif profitability > 0.15:  # 15-20%
        scores["profitability_score"] = 4.0
    elif profitability > 0.10:  # 10-15%
        scores["profitability_score"] = 3.5
    elif profitability > 0.05:  # 5-10%
        scores["profitability_score"] = 3.0
    elif profitability > 0.02:  # 2-5%
        scores["profitability_score"] = 2.0
    elif profitability > 0:     # 0-2%
        scores["profitability_score"] = 1.5
    else:  # Negative (loss)
        scores["profitability_score"] = 1.0
    
    # Leverage Ratio Scoring (lower leverage = lower risk)
    leverage = metrics["leverage_ratio"]
    if leverage < 0.2:      # < 20% debt
        scores["leverage_score"] = 5.0
    elif leverage < 0.4:    # 20-40% debt
        scores["leverage_score"] = 4.0
    elif leverage < 0.6:    # 40-60% debt
        scores["leverage_score"] = 3.0
    elif leverage < 0.8:    # 60-80% debt
        scores["leverage_score"] = 2.0
    else:                   # > 80% debt
        scores["leverage_score"] = 1.0
    
    # Company Scale Scoring
    scale = metrics["company_scale"]
    if scale > 50_000_000:      # > $50M
        scores["scale_score"] = 5.0
    elif scale > 25_000_000:    # $25-50M
        scores["scale_score"] = 4.0
    elif scale > 10_000_000:    # $10-25M
        scores["scale_score"] = 3.5
    elif scale > 5_000_000:     # $5-10M
        scores["scale_score"] = 3.0
    elif scale > 2_000_000:     # $2-5M
        scores["scale_score"] = 2.0
    elif scale > 1_000_000:     # $1-2M
        scores["scale_score"] = 1.5
    else:                       # < $1M
        scores["scale_score"] = 1.0
    
    return scores


def calculate_weighted_risk_score(scores: Dict[str, float]) -> float:
    """Calculate weighted risk score using defined weights"""
    
    # Weights (must sum to 100%)
    profitability_weight = 0.40  # 40%
    leverage_weight = 0.40       # 40%
    scale_weight = 0.20          # 20%
    
    weighted_score = (
        scores["profitability_score"] * profitability_weight +
        scores["leverage_score"] * leverage_weight +
        scores["scale_score"] * scale_weight
    )
    
    return round(weighted_score, 2)


def get_risk_premium_from_score(weighted_score: float) -> float:
    """Map weighted risk score to interest rate premium"""
    
    if weighted_score >= 4.5:      # Excellent (4.5-5.0)
        return 0.50
    elif weighted_score >= 3.5:    # Good (3.5-4.49)
        return 1.25
    elif weighted_score >= 2.5:    # Average (2.5-3.49)
        return 2.75
    elif weighted_score >= 1.5:    # Sub-par (1.5-2.49)
        return 4.50
    else:                          # High-Risk (< 1.5)
        return 6.00  # Should typically be rejected, but allowing with high premium


def calculate_comprehensive_esg_discount(
    industry_code: str,
    annual_revenue: float,
    carbon_emissions: float,
    esg_certifications: str,
    esg_reporting_url: str
) -> tuple[float, Dict[str, Any]]:
    """
    Calculate ESG discount using comprehensive carbon-adjusted model
    Returns: (discount_percentage, esg_details_dict)
    """
    
    # Step 1: Calculate Carbon Performance Score (Quantitative Pillar)
    carbon_score, carbon_details = calculate_carbon_performance_score(
        industry_code, annual_revenue, carbon_emissions
    )
    
    # Step 2: Calculate Qualitative Score (Certifications & Governance)
    qualitative_score, cert_details = calculate_qualitative_esg_score(esg_certifications)
    
    # Step 3: Calculate Weighted ESG Score (70% carbon, 30% qualitative)
    carbon_weight = 0.70
    qualitative_weight = 0.30
    
    final_esg_score = (carbon_score * carbon_weight) + (qualitative_score * qualitative_weight)
    
    # Step 4: Map ESG Score to Interest Rate Discount
    if final_esg_score >= 90:
        discount = 0.75  # ESG Leader
        category = "ESG Leader"
    elif final_esg_score >= 75:
        discount = 0.50  # ESG Strong Performer
        category = "ESG Strong Performer"
    elif final_esg_score >= 50:
        discount = 0.25  # ESG Average Performer
        category = "ESG Average Performer"
    else:
        discount = 0.00  # ESG Laggard
        category = "ESG Laggard"
    
    # Compile detailed ESG analysis
    esg_details = {
        "final_esg_score": round(final_esg_score, 1),
        "esg_category": category,
        "discount_percentage": discount,
        "carbon_performance": {
            "score": carbon_score,
            "weight": carbon_weight,
            "contribution": round(carbon_score * carbon_weight, 1),
            **carbon_details
        },
        "qualitative_performance": {
            "score": qualitative_score,
            "weight": qualitative_weight,
            "contribution": round(qualitative_score * qualitative_weight, 1),
            **cert_details
        },
        "esg_reporting_url": esg_reporting_url if esg_reporting_url else "Not provided"
    }
    
    return discount, esg_details


def calculate_carbon_performance_score(
    industry_code: str, 
    annual_revenue: float, 
    carbon_emissions: float
) -> tuple[int, Dict[str, Any]]:
    """Calculate carbon performance score based on industry benchmarks"""
    
    # Industry benchmarks for carbon intensity (tons CO2e per $M revenue)
    industry_benchmarks = {
        "541": 10,    # Software Development
        "518": 10,    # Technology/Software  
        "311": 250,   # Food Manufacturing
        "336": 180,   # Manufacturing (Auto)
        "441": 80,    # Auto Dealerships
        "221": 400,   # Utilities
        "211": 600,   # Oil & Gas
        "212": 500,   # Mining
        "236": 120,   # Construction
        "484": 150,   # Transportation
        "621": 25,    # Healthcare Services
        "721": 60,    # Hospitality
        "423": 40,    # Wholesale Trade
        "531": 30,    # Real Estate
        "713": 50,    # Entertainment/Gambling
        "111": 200    # Agriculture
    }
    
    # Get first 3 digits of NAICS code for industry classification
    industry_key = industry_code[:3] if len(industry_code) >= 3 else industry_code
    benchmark = industry_benchmarks.get(industry_key, 100)  # Default benchmark
    
    # Calculate emissions intensity (tons CO2e per $M revenue)
    if annual_revenue > 0:
        emissions_intensity = carbon_emissions / (annual_revenue / 1_000_000)
    else:
        emissions_intensity = float('inf')
        
    # Calculate performance vs benchmark
    if emissions_intensity == float('inf') or benchmark == 0:
        performance_vs_benchmark = -100  # Worst case
    else:
        performance_vs_benchmark = ((benchmark - emissions_intensity) / benchmark) * 100
    
    # Score based on performance vs benchmark
    if performance_vs_benchmark > 50:      # > 50% Better
        carbon_score = 100
        performance_category = "> 50% Better than Industry"
    elif performance_vs_benchmark > 25:    # 25-50% Better
        carbon_score = 85
        performance_category = "25-50% Better than Industry"
    elif performance_vs_benchmark > 0:     # 0-25% Better
        carbon_score = 70
        performance_category = "0-25% Better than Industry"
    elif performance_vs_benchmark > -20:   # 0-20% Worse
        carbon_score = 50
        performance_category = "0-20% Worse than Industry"
    else:                                  # > 20% Worse
        carbon_score = 30
        performance_category = "> 20% Worse than Industry"
    
    carbon_details = {
        "emissions_intensity": round(emissions_intensity, 1),
        "industry_benchmark": benchmark,
        "performance_vs_benchmark": f"{performance_vs_benchmark:+.1f}%",
        "performance_category": performance_category,
        "total_emissions": carbon_emissions,
        "annual_revenue_millions": round(annual_revenue / 1_000_000, 1)
    }
    
    return carbon_score, carbon_details


def calculate_qualitative_esg_score(esg_certifications: str) -> tuple[int, Dict[str, Any]]:
    """Calculate qualitative ESG score based on certifications"""
    
    if not esg_certifications or esg_certifications.lower() in ["none", "", "null"]:
        return 0, {"certifications": [], "total_points": 0}
    
    # Parse ESG certifications
    certifications = [cert.strip().upper() for cert in esg_certifications.split(",")]
    
    # Points awarded for recognized certifications
    certification_points = {
        "B-CORP": 40,           # B Corporation certification
        "B CORP": 40,           # Alternative format
        "ISO14001": 25,         # Environmental management
        "ISO 14001": 25,        # Alternative format
        "SBTI": 25,             # Science Based Targets initiative
        "SCIENCE BASED TARGETS": 25,  # Alternative format
        "SA8000": 10,           # Social accountability
        "SA 8000": 10,          # Alternative format
        "LEED": 15,             # Green building
        "ENERGY STAR": 10,      # Energy efficiency
        "FAIR TRADE": 15,       # Fair trade practices
        "CARBON NEUTRAL": 20,   # Carbon neutrality
        "ISO26000": 15,         # Social responsibility
        "ISO 26000": 15,        # Alternative format
        "GRI": 10,              # Global reporting initiative
        "CDP": 10,              # Carbon disclosure project
        "TCFD": 15,             # Task Force on Climate-related Financial Disclosures
        "UN GLOBAL COMPACT": 20 # UN Global Compact
    }
    
    total_points = 0
    recognized_certs = []
    
    for cert in certifications:
        if cert in certification_points:
            points = certification_points[cert]
            total_points += points
            recognized_certs.append({
                "certification": cert,
                "points": points
            })
    
    # Cap maximum qualitative score at 100
    qualitative_score = min(total_points, 100)
    
    cert_details = {
        "certifications": recognized_certs,
        "total_points": total_points,
        "capped_score": qualitative_score,
        "unrecognized_certs": [cert for cert in certifications 
                              if cert not in certification_points]
    }
    
    return qualitative_score, cert_details


def generate_loan_offer(intent_id: str, sender_name: str, amount_value: float,
                       repayment_duration: int, final_interest_rate: float,
                       risk_premium: float, esg_discount: float, weighted_score: float,
                       metrics: Dict[str, float], scores: Dict[str, float],
                       collateral_description: str, esg_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate comprehensive loan offer with all details"""
    
    # Calculate monthly payment (simple interest for demonstration)
    monthly_rate = final_interest_rate / 100 / 12
    monthly_payment = (amount_value * monthly_rate * (1 + monthly_rate)**repayment_duration) / \
                     ((1 + monthly_rate)**repayment_duration - 1) if monthly_rate > 0 else amount_value / repayment_duration
    
    total_interest = (monthly_payment * repayment_duration) - amount_value
    
    # Determine risk category from weighted score
    if weighted_score >= 4.5:
        risk_category = "Excellent"
    elif weighted_score >= 3.5:
        risk_category = "Good"
    elif weighted_score >= 2.5:
        risk_category = "Average"
    elif weighted_score >= 1.5:
        risk_category = "Sub-par"
    else:
        risk_category = "High-Risk"
    
    return {
        "status": "APPROVED",
        "intent_id": intent_id,
        "sender_name": sender_name,
        
        # Loan Terms
        "loan_offer": {
            "principal_amount": amount_value,
            "interest_rate": round(final_interest_rate, 2),
            "term_months": repayment_duration,
            "monthly_payment": round(monthly_payment, 2),
            "total_interest": round(total_interest, 2),
            "total_repayment": round(amount_value + total_interest, 2)
        },
        
        # Interest Rate Breakdown
        "rate_calculation": {
            "base_rate": BANK_POLICIES.base_interest_rate,
            "risk_premium": risk_premium,
            "esg_discount": esg_discount,
            "final_rate": round(final_interest_rate, 2)
        },
        
        # Risk Assessment Details
        "risk_analysis": {
            "weighted_risk_score": weighted_score,
            "risk_category": risk_category,
            "financial_metrics": {
                "profitability_margin": f"{metrics['profitability_margin']:.2%}",
                "leverage_ratio": f"{metrics['leverage_ratio']:.2%}",
                "company_scale": f"${metrics['company_scale']:,.0f}"
            },
            "metric_scores": {
                "profitability_score": scores['profitability_score'],
                "leverage_score": scores['leverage_score'],
                "scale_score": scores['scale_score']
            }
        },
        
        # ESG Analysis (if available)
        "esg_analysis": esg_details if esg_details else {
            "final_esg_score": "Not calculated",
            "esg_category": "Not assessed",
            "discount_percentage": esg_discount
        },
        
        # Additional Terms
        "terms_and_conditions": {
            "collateral_required": collateral_description if collateral_description else "To be determined",
            "origination_fee": round(amount_value * 0.01, 2),  # 1% origination fee
            "prepayment_penalty": "None for payments > 20% of principal",
            "draw_period": "24 months" if repayment_duration > 24 else f"{repayment_duration} months"
        },
        
        # Next Steps
        "next_steps": [
            "Formal application submission required",
            "Credit verification and documentation review",
            "Collateral appraisal (if applicable)", 
            "Final underwriting approval",
            "Loan agreement execution"
        ],
        
        "offer_expires": "30 days from generation",
        "generated_at": "2024-01-15T12:00:00Z"  # Would be actual timestamp
    }


def calculate_final_approved_amount(
    intent_id: str,
    sender_name: str,
    requested_amount: float,
    annual_revenue: float,
    weighted_risk_score: float,
    final_esg_score: float
) -> Dict[str, Any]:
    """
    Calculate final approved amount using Dynamic Lending Ratio Model
    
    Args:
        intent_id: Application identifier
        sender_name: Company name
        requested_amount: Amount requested by the company
        annual_revenue: Company's annual revenue
        weighted_risk_score: Previously calculated weighted risk score (1-5)
        final_esg_score: Previously calculated ESG score (0-100)
    
    Returns:
        Dictionary with final approved amount and calculation details
    """
    
    try:
        # Step 1: Get base lending ratio from bank policies
        base_ratio = BANK_POLICIES.base_lending_ratio  # 15%
        
        # Step 2: Calculate Financial Risk Adjustment
        financial_adjustment = get_financial_risk_adjustment(weighted_risk_score)
        
        # Step 3: Calculate ESG Opportunity Adjustment  
        esg_adjustment = get_esg_opportunity_adjustment(final_esg_score)
        
        # Step 4: Calculate Adjusted Lending Ratio
        adjusted_ratio = base_ratio + financial_adjustment + esg_adjustment
        
        # Step 5: Calculate Maximum Approved Amount
        max_approved_amount = annual_revenue * adjusted_ratio
        
        # Step 6: Apply absolute limits from bank policies
        max_approved_amount = min(max_approved_amount, BANK_POLICIES.max_credit_limit_absolute)
        max_approved_amount = max(max_approved_amount, BANK_POLICIES.min_credit_limit)
        
        # Step 7: Final Decision Logic - compare requested vs calculated max
        if requested_amount <= max_approved_amount:
            final_approved_amount = requested_amount
            approval_reason = "Requested amount is within calculated risk appetite"
            approval_status = "FULLY_APPROVED"
        else:
            final_approved_amount = max_approved_amount
            approval_reason = f"Requested amount (${requested_amount:,.2f}) exceeds calculated maximum (${max_approved_amount:,.2f})"
            approval_status = "PARTIALLY_APPROVED"
        
        # Determine risk and ESG categories for reporting
        risk_category = get_risk_category_from_score(weighted_risk_score)
        esg_category = get_esg_category_from_score(final_esg_score)
        
        return {
            "status": "SUCCESS",
            "intent_id": intent_id,
            "sender_name": sender_name,
            "approval_decision": {
                "requested_amount": requested_amount,
                "final_approved_amount": final_approved_amount,
                "approval_status": approval_status,
                "approval_reason": approval_reason
            },
            "calculation_details": {
                "annual_revenue": annual_revenue,
                "base_lending_ratio": base_ratio,
                "financial_risk_adjustment": financial_adjustment,
                "esg_opportunity_adjustment": esg_adjustment,
                "adjusted_lending_ratio": adjusted_ratio,
                "calculated_maximum": max_approved_amount,
                "weighted_risk_score": weighted_risk_score,
                "risk_category": risk_category,
                "final_esg_score": final_esg_score,
                "esg_category": esg_category
            },
            "lending_capacity": {
                "percentage_of_revenue": f"{adjusted_ratio:.1%}",
                "utilization_rate": f"{final_approved_amount / max_approved_amount:.1%}" if max_approved_amount > 0 else "0.0%",
                "remaining_capacity": max(0, max_approved_amount - final_approved_amount)
            }
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": f"Final approved amount calculation failed: {str(e)}",
            "intent_id": intent_id,
            "sender_name": sender_name
        }


def get_financial_risk_adjustment(weighted_risk_score: float) -> float:
    """Get financial risk adjustment based on weighted risk score"""
    
    if weighted_risk_score >= 4.5:      # Excellent (4.5-5.0)
        return 0.05  # +5.0%
    elif weighted_risk_score >= 3.5:    # Good (3.5-4.49)
        return 0.025  # +2.5%
    elif weighted_risk_score >= 2.5:    # Average (2.5-3.49)
        return 0.0   # +0.0%
    elif weighted_risk_score >= 1.5:    # Sub-par (1.5-2.49)
        return -0.05  # -5.0%
    else:                               # High-Risk (< 1.5)
        return -0.10  # -10.0%


def get_esg_opportunity_adjustment(final_esg_score: float) -> float:
    """Get ESG opportunity adjustment based on final ESG score"""
    
    if final_esg_score >= 90:      # ESG Leader (90-100)
        return 0.025  # +2.5%
    elif final_esg_score >= 75:    # ESG Strong Performer (75-89)
        return 0.015  # +1.5%
    elif final_esg_score >= 50:    # ESG Average Performer (50-74)
        return 0.0    # +0.0%
    else:                          # ESG Laggard (< 50)
        return -0.01  # -1.0%


def get_risk_category_from_score(weighted_risk_score: float) -> str:
    """Get risk category string from weighted risk score"""
    
    if weighted_risk_score >= 4.5:
        return "Excellent"
    elif weighted_risk_score >= 3.5:
        return "Good"
    elif weighted_risk_score >= 2.5:
        return "Average"
    elif weighted_risk_score >= 1.5:
        return "Sub-par"
    else:
        return "High-Risk"


def get_esg_category_from_score(final_esg_score: float) -> str:
    """Get ESG category string from final ESG score"""
    
    if final_esg_score >= 90:
        return "ESG Leader"
    elif final_esg_score >= 75:
        return "ESG Strong Performer"
    elif final_esg_score >= 50:
        return "ESG Average Performer"
    else:
        return "ESG Laggard"


def calculate_approved_repayment_duration(
    intent_id: str,
    sender_name: str,
    preferred_repayment_duration: int,
    purpose: str,
    weighted_risk_score: float,
    final_approved_amount: float
) -> Dict[str, Any]:
    """
    Calculate approved repayment duration based on loan purpose, risk profile, and bank policies.
    
    Args:
        intent_id: Application identifier
        sender_name: Company name
        preferred_repayment_duration: Client's preferred duration in months
        purpose: Loan purpose (e.g., "working capital", "equipment purchase")
        weighted_risk_score: Previously calculated weighted risk score (1-5)
        final_approved_amount: Previously calculated approved loan amount
    
    Returns:
        Dictionary with approved repayment duration and calculation details
    """
    
    try:
        # Step 1: Normalize and identify loan purpose
        normalized_purpose = normalize_loan_purpose(purpose)
        
        # Step 2: Get policy maximum duration for this purpose
        purpose_limits = get_purpose_duration_limits(normalized_purpose)
        
        if not purpose_limits:
            # Default limits for unknown purposes
            purpose_limits = {"max_duration": 36, "min_duration": 12}
            purpose_status = "UNKNOWN_PURPOSE_DEFAULT_APPLIED"
        else:
            purpose_status = "PURPOSE_POLICY_APPLIED"
        
        policy_max_duration = purpose_limits["max_duration"]
        policy_min_duration = purpose_limits["min_duration"]
        
        # Step 3: Calculate risk-adjusted maximum duration
        risk_adjustment_factor = get_risk_duration_adjustment_factor(weighted_risk_score)
        risk_category = get_risk_category_from_score(weighted_risk_score)
        
        # Apply risk adjustment to policy maximum
        risk_adjusted_max = int(policy_max_duration * risk_adjustment_factor)
        
        # Step 4: Determine bank's final maximum term
        bank_final_max = min(policy_max_duration, risk_adjusted_max)
        
        # Ensure it doesn't go below policy minimum
        bank_final_max = max(bank_final_max, policy_min_duration)
        
        # Step 5: Make final decision
        if preferred_repayment_duration <= bank_final_max and preferred_repayment_duration >= policy_min_duration:
            final_approved_duration = preferred_repayment_duration
            approval_status = "FULLY_APPROVED"
            approval_reason = "Requested duration is within policy and risk limits"
        elif preferred_repayment_duration > bank_final_max:
            final_approved_duration = bank_final_max
            approval_status = "DURATION_REDUCED"
            approval_reason = f"Requested duration ({preferred_repayment_duration} months) exceeds risk-adjusted maximum ({bank_final_max} months)"
        elif preferred_repayment_duration < policy_min_duration:
            final_approved_duration = policy_min_duration
            approval_status = "DURATION_EXTENDED"
            approval_reason = f"Requested duration ({preferred_repayment_duration} months) is below policy minimum ({policy_min_duration} months)"
        else:
            final_approved_duration = bank_final_max
            approval_status = "POLICY_APPLIED"
            approval_reason = "Standard policy duration applied"
        
        # Calculate monthly payment estimate (for reference)
        if final_approved_amount > 0 and final_approved_duration > 0:
            estimated_monthly_payment = final_approved_amount / final_approved_duration
        else:
            estimated_monthly_payment = 0.0
        
        return {
            "status": "SUCCESS",
            "intent_id": intent_id,
            "sender_name": sender_name,
            "duration_decision": {
                "preferred_duration_months": preferred_repayment_duration,
                "final_approved_duration_months": final_approved_duration,
                "approval_status": approval_status,
                "approval_reason": approval_reason
            },
            "calculation_details": {
                "loan_purpose": purpose,
                "normalized_purpose": normalized_purpose,
                "purpose_status": purpose_status,
                "policy_max_duration": policy_max_duration,
                "policy_min_duration": policy_min_duration,
                "weighted_risk_score": weighted_risk_score,
                "risk_category": risk_category,
                "risk_adjustment_factor": risk_adjustment_factor,
                "risk_adjusted_max": risk_adjusted_max,
                "bank_final_max": bank_final_max
            },
            "payment_details": {
                "final_approved_amount": final_approved_amount,
                "estimated_monthly_payment": round(estimated_monthly_payment, 2),
                "total_estimated_payments": final_approved_duration
            },
            "policy_compliance": {
                "within_purpose_limits": policy_min_duration <= final_approved_duration <= policy_max_duration,
                "risk_adjustment_applied": risk_adjustment_factor < 1.0,
                "duration_change_required": preferred_repayment_duration != final_approved_duration
            }
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": f"Repayment duration calculation failed: {str(e)}",
            "intent_id": intent_id,
            "sender_name": sender_name
        }


def normalize_loan_purpose(purpose: str) -> str:
    """Normalize loan purpose string to match policy keys"""
    
    if not purpose:
        return "general_business_purposes"
    
    # Convert to lowercase and replace common variations
    normalized = purpose.lower().strip()
    
    # Map common variations to standard purposes
    purpose_mappings = {
        "working capital": "working_capital",
        "working_capital": "working_capital",
        "cash flow": "cash_flow_management",
        "cash_flow_management": "cash_flow_management",
        "inventory": "inventory_financing",
        "inventory_financing": "inventory_financing",
        "equipment": "equipment_purchase",
        "equipment_purchase": "equipment_purchase",
        "equipment financing": "equipment_purchase",
        "expansion": "business_expansion",
        "business_expansion": "business_expansion",
        "business expansion": "business_expansion",
        "seasonal": "seasonal_financing",
        "seasonal_financing": "seasonal_financing",
        "bridge": "bridge_financing",
        "bridge_financing": "bridge_financing",
        "acquisition": "acquisition_financing",
        "acquisition_financing": "acquisition_financing",
        "refinancing": "refinancing",
        "refinance": "refinancing",
        "debt consolidation": "debt_consolidation",
        "debt_consolidation": "debt_consolidation",
        "consolidation": "debt_consolidation",
        "general": "general_business_purposes",
        "general_business_purposes": "general_business_purposes",
        "general business purposes": "general_business_purposes",
        "business purposes": "general_business_purposes"
    }
    
    # Check for exact matches first
    if normalized in purpose_mappings:
        return purpose_mappings[normalized]
    
    # Check for partial matches
    for key, value in purpose_mappings.items():
        if key in normalized or normalized in key:
            return value
    
    # Default to general business purposes if no match found
    return "general_business_purposes"


def get_purpose_duration_limits(normalized_purpose: str) -> Dict[str, int]:
    """Get duration limits for a specific loan purpose"""
    
    return BANK_POLICIES.loan_purpose_duration_limits.get(normalized_purpose)


def get_risk_duration_adjustment_factor(weighted_risk_score: float) -> float:
    """Get duration adjustment factor based on risk score"""
    
    if weighted_risk_score >= 4.5:      # Excellent (4.5-5.0)
        return 1.0   # No adjustment (100%)
    elif weighted_risk_score >= 3.5:    # Good (3.5-4.49)
        return 0.9   # Cap at 90% of policy maximum
    elif weighted_risk_score >= 2.5:    # Average (2.5-3.49)
        return 0.75  # Cap at 75% of policy maximum
    elif weighted_risk_score >= 1.5:    # Sub-par (1.5-2.49)
        return 0.5   # Cap at 50% of policy maximum
    else:                               # High-Risk (< 1.5)
        return 0.25  # Cap at 25% of policy maximum (or manual review)


def generate_loan_offer_json(
    intent_id: str,
    sender_name: str,
    interest_rate_result: Dict[str, Any],
    approved_amount_result: Dict[str, Any],
    duration_result: Dict[str, Any],
    esg_impact_summary: str
) -> Dict[str, Any]:
    """
    Generate comprehensive loan offer JSON response based on results from previous tools.
    
    Args:
        intent_id: Application identifier
        sender_name: Company name
        interest_rate_result: Result from calculate_interest_rate_and_offer
        approved_amount_result: Result from calculate_final_approved_amount
        duration_result: Result from calculate_approved_repayment_duration
    
    Returns:
        Complete loan offer JSON response
    """
    
    try:
        import uuid
        from datetime import datetime
        
        # Generate unique offer ID
        offer_id = str(uuid.uuid4())
        current_timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Check for errors in input tool results first
        if interest_rate_result.get('status') == 'ERROR':
            raise Exception(f"Interest rate calculation failed: {interest_rate_result.get('error', 'Unknown error')}")
        
        if approved_amount_result.get('status') == 'ERROR':
            raise Exception(f"Approved amount calculation failed: {approved_amount_result.get('error', 'Unknown error')}")
            
        if duration_result.get('status') == 'ERROR':
            raise Exception(f"Duration calculation failed: {duration_result.get('error', 'Unknown error')}")
        
        # Extract key data from tool results with error checking
        try:
            approved_amount = approved_amount_result['approval_decision']['final_approved_amount']
        except (KeyError, TypeError) as e:
            raise Exception(f"Missing or invalid approved_amount_result structure: {e}. Result keys: {list(approved_amount_result.keys()) if isinstance(approved_amount_result, dict) else 'Not a dict'}")
            
        try:
            interest_rate = interest_rate_result['rate_calculation']['final_rate']
        except (KeyError, TypeError) as e:
            raise Exception(f"Missing or invalid interest_rate_result structure: {e}. Result keys: {list(interest_rate_result.keys()) if isinstance(interest_rate_result, dict) else 'Not a dict'}")
            
        try:
            duration_months = duration_result['duration_decision']['final_approved_duration_months']
        except (KeyError, TypeError) as e:
            raise Exception(f"Missing or invalid duration_result structure: {e}. Result keys: {list(duration_result.keys()) if isinstance(duration_result, dict) else 'Not a dict'}")
        
        # Determine overall approval status
        try:
            amount_status = approved_amount_result['approval_decision']['approval_status']
            duration_status = duration_result['duration_decision']['approval_status']
        except (KeyError, TypeError) as e:
            raise Exception(f"Missing status information in results: {e}")
        
        if amount_status == "FULLY_APPROVED" and duration_status == "FULLY_APPROVED":
            offer_status = "OFFER_EXTENDED"
        elif amount_status == "PARTIALLY_APPROVED" or duration_status in ["DURATION_REDUCED", "DURATION_EXTENDED"]:
            offer_status = "OFFER_EXTENDED_WITH_MODIFICATIONS"
        else:
            offer_status = "OFFER_EXTENDED"
        
        # Build simplified loan offer JSON with only required fields plus ESG impact summary
        loan_offer_json = {
            "offer_id": offer_id,
            "intent_id": intent_id,
            "created_at": current_timestamp,
            "protocol_version": "WFAP-1.0",
            "bank_agent_id": "WF-BANK-AGENT-001",
            "status": offer_status,
            "amount_approved": int(approved_amount),  # Convert to int as shown in example
            "currency": "USD",
            "interest_rate_annual": round(interest_rate, 2),
            "repayment_duration_months": duration_months,
            "repayment_schedule": "amortizing",
            "esg_impact_summary": esg_impact_summary
        }
        
        return loan_offer_json
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": f"Loan offer JSON generation failed: {str(e)}",
            "intent_id": intent_id,
            "sender_name": sender_name
        }

def negotiate_loan(negotiation_score: float, preferred_interest_rate: float, annual_interest_rate: float, negotiation_interest_rate: float):
    discount = negotiation_score*0.04
    return (max(negotiation_interest_rate, (annual_interest_rate - discount)))