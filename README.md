# A2A Credit Line Request Demo
This document describes a multi-agent application demonstrating Wells Fargo Agent Protocol (WFAP) for agent-to-agent credit line negotiations.

This application contains two main agents:
*   **Consumer Agent**: The primary agent that sends credit line requests to bank agents.
*   **Wells Fargo Bank Agent**: A bank agent that processes credit requests and generates competitive offers with ESG assessments.

## Setup and Deployment

### Prerequisites

Before running the application locally, ensure you have the following installed:

1. **uv:** The Python package management tool used in this project. Follow the installation guide: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
2. **python 3.13** Python 3.13 is required to run a2a-sdk 
3. **set up .env** 

Create a `.env` file in the root of the `a2a_friend_scheduling` directory with your Google API Key:
```
GOOGLE_API_KEY="your_api_key_here" 
```

## Run the Agents

You will need to run each agent in a separate terminal window. The first time you run these commands, `uv` will create a virtual environment and install all necessary dependencies before starting the agent.

### Terminal 1: Run Wells Fargo Bank Agent
```bash
cd loan_agent_adk
uv venv
source .venv/bin/activate
uv run --active .
```

### Terminal 2: Run Consumer Agent
```bash
cd host_agent_adk
uv venv
source .venv/bin/activate
uv run --active adk web      
```

## Interact with the Consumer Agent

Once both agents are running, you can interact with the Consumer Agent to request credit lines. The Consumer Agent will:

1. **Gather Company Information**: Collect details about your company including name, industry, annual revenue, years in business
2. **Define Credit Requirements**: Specify the amount, duration, and purpose of the credit line
3. **Set ESG Preferences**: Configure environmental and social impact criteria
4. **Send Requests**: Automatically send structured credit requests to all available bank agents
5. **Compare Offers**: Analyze received offers based on interest rates, ESG scores, and risk assessments
6. **Select Best Offer**: Choose the optimal offer using a scoring algorithm that considers financial terms and ESG impact

### Example Interaction:
```
"I need a $500,000 credit line for my technology company. We've been in business for 8 years with $5M annual revenue. We want to focus on renewable energy projects."
```

The system will process this request, generate offers with ESG assessments, and provide a comprehensive comparison of all available options.

## Wells Fargo Agent Protocol (WFAP)

This implementation follows the Wells Fargo Agent Protocol for secure, structured communication between financial agents:

### Key Features:
- **Digital Signatures**: All requests and offers are digitally signed for authentication
- **ESG Integration**: Environmental, Social, and Governance factors are automatically assessed
- **Carbon-Adjusted Rates**: Interest rates are adjusted based on carbon footprint calculations
- **Regulatory Compliance**: Built-in compliance checks for banking regulations
- **Risk Assessment**: Automated risk evaluation based on company profile and industry

### Protocol Schema:
The complete protocol schema is defined in `artifacts/arch/schema.json` and includes:
- Intent structure for credit requests
- Offer structure for bank responses
- ESG impact assessments
- Regulatory compliance data
- Digital signature verification

## Architecture

### Consumer Agent (Host Agent)
- Sends structured credit requests to bank agents
- Collects and compares multiple offers
- Implements scoring algorithm for offer selection
- Handles ESG preference configuration

### Wells Fargo Bank Agent (Loan Agent)
- Processes incoming credit requests
- Generates competitive offers with ESG assessments
- Performs risk assessment and compliance checks
- Creates carbon-adjusted interest rates

## References
- https://github.com/google/a2a-python
- https://codelabs.developers.google.com/intro-a2a-purchasing-concierge#1
- Wells Fargo Agent Protocol Documentation (see `artifacts/arch/schema.json`)
