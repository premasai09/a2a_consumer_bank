# WFAP Demo Script

## Demo Scenario: Tech Company Credit Line Request

### Company Profile:
- **Company Name**: GreenTech Solutions
- **Industry**: Renewable Energy Technology
- **Annual Revenue**: $5,000,000
- **Years in Business**: 8
- **Credit Score**: 750

### Credit Request:
- **Amount**: $500,000
- **Duration**: 24 months
- **Purpose**: Expand solar panel manufacturing facility
- **ESG Weight**: 0.4 (40% importance on ESG factors)

## Expected Demo Flow:

### 1. Consumer Agent Interaction
```
User: "I need a $500,000 credit line for my renewable energy company. We've been in business for 8 years with $5M annual revenue. We want to expand our solar panel manufacturing."

Consumer Agent: "I'll help you request a credit line. Let me gather the details and send requests to available bank agents."
```

### 2. Credit Request Generation
The Consumer Agent will create a structured Intent with:
- Company profile information
- Credit requirements
- ESG preferences (focusing on renewable energy)
- Digital signature for authentication

### 3. Bank Agent Processing
The Wells Fargo Bank Agent will:
- Verify the digital signature
- Assess creditworthiness based on company profile
- Calculate interest rate (adjusted for credit score, business history, revenue)
- Generate ESG impact assessment
- Perform compliance checks
- Create carbon-adjusted interest rate
- Generate structured offer with digital signature

### 4. Offer Comparison
The Consumer Agent will receive and compare offers showing:
- Approved amount and interest rates
- ESG scores and carbon footprint
- Risk assessments
- Regulatory compliance status
- Sustainability initiatives

### 5. Best Offer Selection
The system will select the best offer based on:
- Low interest rate (40% weight)
- Low carbon-adjusted rate (30% weight)
- High ESG score (20% weight)
- Low risk level (10% weight)

## Expected Output:

```
🏆 BEST OFFER SELECTED: Wells Fargo Bank

📊 Offer Details:
   • Approved Amount: $450,000.00
   • Interest Rate: 4.80%
   • Repayment Period: 24 months
   • ESG Score: 92/100
   • Carbon-Adjusted Rate: 5.15%
   • Risk Level: low

🌱 ESG Summary: Wells Fargo's ESG-optimized credit offering supports renewable energy technology sector growth while maintaining strong environmental standards. This loan contributes to sustainable business practices with a focus on renewable energy initiatives and community development. Our carbon offset programs will neutralize 85.3 tons of CO2 equivalent over the loan term, supporting the company's sustainability goals.

💡 Selection Criteria: Low interest rate, high ESG score, low carbon footprint, and acceptable risk level.
```

## Key Features Demonstrated:

1. **Structured Communication**: WFAP protocol ensures standardized, secure communication
2. **ESG Integration**: Automatic environmental impact assessment and carbon-adjusted rates
3. **Digital Signatures**: Authentication and verification of all communications
4. **Risk Assessment**: Comprehensive evaluation of creditworthiness and industry risk
5. **Regulatory Compliance**: Built-in compliance checks for banking regulations
6. **Automated Decision Making**: AI-powered offer comparison and selection

## Technical Implementation:

- **Intent Processing**: JSON-based structured credit requests
- **Offer Generation**: Automated calculation of terms based on risk profiles
- **ESG Scoring**: LLM-generated environmental impact summaries
- **Digital Signatures**: SHA256-based authentication (simplified for demo)
- **Agent Communication**: A2A protocol for secure inter-agent messaging
