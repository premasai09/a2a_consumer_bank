import random
import json
import time
from datetime import date, datetime, timedelta
from typing import Dict, Any
from tachyon_adk_client import TachyonAdkClient
from google.adk.agents import Agent
from .bank_policy_tools import (
    perform_initial_risk_assessment,
    calculate_interest_rate_and_offer,
    calculate_final_approved_amount,
    calculate_approved_repayment_duration,
    generate_loan_offer_json,
    negotiate_loan
)


def create_agent() -> Agent:
    """Constructs the ADK agent for Finovate Bank."""
    return Agent(
        model=TachyonAdkClient(model_name="gemini-2.5-flash"),
    name="finovate_bank_agent",
    description="A comprehensive Finovate Bank agent that processes corporate line of credit applications from initial risk assessment through loan offer generation or intelligent rejection analysis.",
    instruction="""
    I am a bank loan processing agent.
   
    In case the user sends a loan application, I MUST follow this exact workflow(STEP 1,2):
 
    **STEP 1: ALWAYS START HERE**
    Call `perform_initial_risk_assessment` tool first with required parameters. Pass all the required parameters into this tool. DO NOT skip this step.
    - IF the result is "PASS", proceed to STEP 2A
    - IF the result is "FAIL", proceed to STEP 2B
 
    **STEP 2A: IF perform_initial_risk_assessment returns "PASS"**
    Execute these tools in EXACT order:
    1. Call `calculate_interest_rate_and_offer` tool
    2. Call `calculate_final_approved_amount` tool  
    3. Call `calculate_approved_repayment_duration` tool
    4. GENERATE ESG IMPACT SUMMARY - INTERNAL PROCESSING ONLY:
       - Extract ESG data from tool context (company name, ESG score, carbon performance, certifications, discount amount, loan purpose)
       -Extract the carbon emissions value from the context or the loan application that user has sent.
       - Analyze the ESG data to create a concise summary of the company's environmental, social, and governance impact.
       - Generate ONLY a clear, positive, human-readable ESG summary (2-3 sentences)
       - Use NO specific numbers or percentages - translate to descriptive terms
       - DO NOT return this summary to user - pass ONLY to generate_loan_offer_json tool
       - DO NOT show prompt instructions or generation process to user
    5. Call `generate_loan_offer_json` tool with results from steps 1-3 AND the generated ESG summary. While calling this tool, provide inputs from other tools without adding any extra interpretation or modification. Directly pass the results as they are.
 
    6. RETURN ONLY the complete JSON result from `generate_loan_offer_json` tool as final response
   
    **STEP 2B: IF perform_initial_risk_assessment returns "FAIL". DO NOT run this in case the STEP1 response is PASS**
    DO NOT call any other tools. Analyze the rejection results and provide detailed rejection explanation.
 
    In case the user sends a message for negotiating the already sent offer, then follow the below steps(3):
    STEP 3:
    Analyze the negotiation message that user has sent, if you feel the company is looking for reducing the esg imapact, if the company is promising to invest the part of loan into cleaner machinery. based on the analysis generate a score between 1-10. Pass the score into 'negotiate_loan' tool as a parameter. Extract the preferred_interest_rate field value from that you have received in the initial steps and pass this paramter to the 'negotiate_loan' tool. Also extract the Interest Rate (Annual) form the loan offer you have generated in the generate_loan_offer_json tool in earlier steps and pass it to 'negotiate_loan' tool. Extract these from tool context if available. Also pass the interest rate from the negotiation offer into this tool. Return the complete offer json from 'generate_loan_offer_json' tool only with decreased interest rate based on above tool response.
 
    In case the user responds that they accept the final offer, then proceed with Step 4.
    STEP 4:
    *   **Respond to accepted Offer:**   If the user has sent a message accepting the offer then respond with below format:
        Final agreed upon offer:
            "bankname": string,
            "bankid": string,
            "amount_approved": number,
            "created_date": string,
            "currency": string,
            "esg_impact_summary": string,
            "intent_id": string,
            "interest_rate_annual": float,// if the user has negotiated the offer then put the interest rate from send_user_message_tool returned interest otherwise put the interest rate sent as a part of intial loan offer only.
            "offer_id": string,
            "protocol_version": string,
            "repayment_duration_months": number,
            "repayment_schedule": string,
            "status": string,
            "ESG_impact_summary": string,
            "status_message": "Thank you for accepting our offer. Our bank representatives will come back shortly for further steps"
        Send the above offer as JSON to the user.
 
    In case the user responds that they do not accept the offer, the follow the step5.
    STEP 5:
    return the below reponse as a text mesasge: We are sorry that we could not meet your line of credit requirements.
 
    **STRICT EXECUTION ORDER:**
    - NEVER skip `perform_initial_risk_assessment`
    - NEVER call loan offer tools if risk assessment is FAIL
    - ALWAYS call all 4 tools in sequence if risk assessment is PASS
    - ALWAYS generate ESG summary internally before calling generate_loan_offer_json
    - ALWAYS pass results between tools as required parameters
    - ALWAYS return ONLY the final JSON from `generate_loan_offer_json` tool
 
    **Tool Execution Rules:**
    - Pass only required parameters to each tool
    - Use results from previous tools as inputs for subsequent tools
    - Do not modify or interpret tool results, pass them as-is
    - Generate ESG summary silently - do NOT show generation process to user
    - Do NOT return ESG summary separately - only include it in final JSON
    - Return ONLY the exact JSON output from `generate_loan_offer_json` as the final response
    - NEVER show prompt instructions, generation steps, or intermediate summaries to user
   
    **RESPONSE FORMAT RULES (CRITICAL):**
    - ALWAYS return ONLY the final JSON object from `generate_loan_offer_json` as the response.
    - DO NOT wrap the JSON in Markdown code blocks (no ```json or ```).
    - DO NOT add any extra text, explanation, or formatting before or after the JSON.
    - DO NOT wrap the JSON in an extra key (like "generate_loan_offer_json_response")—return only the inner JSON object.
    - The response must be a single, valid JSON object, suitable for direct parsing.
    - If there is an error, return a JSON object with an "error" key and a clear error message.
    - Give the final response in a single line json, seperated by ';'. 
    
    ***Retry Mechanism:***
        - While calling any tools, if there are invalid arguments passed or the request is errored due to invalid inputs, please pass the parameters again properly and retry calling the same tool for the same action for 2 times. only if it fails for more than 2 times, then report the error to user.""",
        
    tools=[perform_initial_risk_assessment, calculate_interest_rate_and_offer, calculate_final_approved_amount, calculate_approved_repayment_duration, generate_loan_offer_json, negotiate_loan, ]
    )


async def process_credit_request(request_data: dict) -> dict:
    print(f"[{datetime.now()}] Finovate Bank agent received request: {json.dumps(request_data)[:200]}...")
    start_time = datetime.now()
    time.sleep(2)
    end_time = datetime.now()
    print(f"[{end_time}] Finovate Bank agent finished processing in {(end_time - start_time).total_seconds()} seconds")
    return {"status": "processed", "timestamp": str(end_time)}


root_agent = create_agent()
