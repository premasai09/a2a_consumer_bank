# CrediFlow - A2A Consumer Banking System

**🏦 Enterprise-Grade Agent-to-Agent Banking Network**  
*Built with Google's Agent Development Kit (ADK) & A2A Protocol Framework*

**Created by CreditAvengers**

## 👥 Team Members
- **Prema Sai**
- **Sailesh R** 
- **Prem Reddy**
- **Hamsika M**

---

## 🎯 Developer Overview

Welcome to **CrediFlow** - a sophisticated proof-of-concept demonstrating how modern financial institutions can leverage AI agents for automated corporate credit processing. As a developer, you'll find this system showcases real-world applications of:

- **Multi-agent orchestration** using Google ADK
- **Distributed microservices architecture** with agent-to-agent communication
- **Complex business logic** including ESG scoring and risk assessment
- **Real-time web interfaces** with Flask and modern JavaScript
- **Production-ready patterns** including error handling, logging, and scalability considerations
---

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                A2A Banking Network                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐    WFAP Protocol    ┌─────────────┐ │
│  │   Host Agent    │◄──────────────────►│ Bank Agents │ │
│  │   (Consumer)    │                     │             │ │
│  │                 │    JSON-RPC over    │ ┌─────────┐ │ │
│  │ • Web UI        │      HTTP/HTTPS     │ │ Bank 1  │ │ │
│  │ • Chat Interface│                     │ │ Bank 2  │ │ │
│  │ • Offer Analysis│                     │ │ Bank 3  │ │ │
│  │ • Negotiation   │                     │ │ Bank 4  │ │ │
│  └─────────────────┘                     │ │ Bank 5  │ │ │
│                                          │ └─────────┘ │ │
│                                          └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Bank Agent Network

Each bank agent operates as an autonomous microservice:

- **CloudTrust Financial** (Port 10002) - Conservative ESG-focused lending
- **Finovate Bank** (Port 10003) - Competitive rates with ESG integration  
- **Zentra Bank** (Port 10004) - Specialized lending solutions
- **NexVault Bank** (Port 10005) - Digital-first banking approach
- **Byte Bank** (Port 10006) - Technology-focused lending

---

## 🚀 Quick Start for Developers

### Prerequisites

```bash
# Required
Python 3.8+
Wells Fargo API Gateway Access (for production integration)
```

### Installation & Setup

```bash
# 1. Clone and navigate
git clone <repository-url>
cd a2a_consumer_bank/code/src

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up SSL certificates (for production)
# Place the Wells Fargo certificate in code/src directory
# Copy WFBTrust.pem to code/src/
# Example: code/src/WFBTrust.pem

# 4. Set up environment variables
# Create .env file with the following variables:
```

```bash
# .env file configuration
# Wells Fargo API Gateway Configuration
USE_API_GATEWAY=false
APIGEE_URL=https://api.wellsfargo.com
BASE_URL=https://your-base-url.com
USE_CASE_ID=your_use_case_id
API_KEY=your_api_key
CONSUMER_KEY=your_consumer_key
CONSUMER_SECRET=your_consumer_secret
CERTS_PATH=./WFBTrust.pem
```

**Environment Variables Explained:**

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `USE_API_GATEWAY` | Enable Wells Fargo API Gateway integration | ✅ Yes | `true/false` |
| `APIGEE_URL` | Wells Fargo Apigee gateway URL | ✅ Yes | `https://api.wellsfargo.com` |
| `BASE_URL` | Base URL for your application | ✅ Yes | `https://yourapp.com` |
| `USE_CASE_ID` | Wells Fargo use case identifier | ✅ Yes | `UC_CREDIT_001` |
| `API_KEY` | Wells Fargo API key | ✅ Yes | `your_api_key` |
| `CONSUMER_KEY` | OAuth consumer key | ✅ Yes | `your_consumer_key` |
| `CONSUMER_SECRET` | OAuth consumer secret | ✅ Yes | `your_consumer_secret` |
| `CERTS_PATH` | Path to WFBTrust.pem certificate | ✅ Yes | `./WFBTrust.pem` |

### Launch Options

#### 🎯 **Option 1: Full System (Recommended for Development)**
```bash
cd code/src
start_banking_system.bat
```
**What this does:**
- Starts all 5 bank agents on ports 10002-10006
- Launches the consumer web interface on port 8000
- Provides complete system for testing and development

#### 🔧 **Option 2: Individual Components (Advanced Development)**
```bash
# Terminal 1: Start individual bank agents
python -m bank_agent_1_adk.main  # CloudTrust Financial
python -m bank_agent_2_adk.main  # Finovate Bank
python -m bank_agent_3_adk.main  # Zentra Bank
python -m bank_agent_4_adk.main  # NexVault Bank
python -m bank_agent_5_adk.main  # Byte Bank

# Terminal 2: Start consumer interface
python -m host_agent_adk.start_custom_ui
```

#### 🌐 **Option 3: Web UI Only (Frontend Development)**
```bash
python -m host_agent_adk.start_custom_ui
---

## 🏢 Company Configuration System

### Default Company Profile

The system ships with a default healthcare company profile located at:
```bash
code/src/host_agent_adk/company_config.py
```

### 📝 How to Customize Company Configurations

#### Method 1: Modify the Default Profile

Edit `code/src/host_agent_adk/company_config.py`:

```python
class CorporateConfig:
    def __init__(self):
        # Core Protocol Fields
        self.intent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.nonce = secrets.token_hex(16)
        self.protocol_version = "WFAP-1.0"
        
        # 🏢 COMPANY IDENTITY - Customize these fields
        self.sender_id = "YOUR_DUNS_NUMBER"           # D&B DUNS number
        self.sender_name = "Your Company Name Inc."   # Legal company name
        self.company_registration_number = "STATE-123456789"  # State registration
        self.jurisdiction = "US-NY"                   # US state (US-CA, US-TX, etc.)
        
        # 🏭 INDUSTRY CLASSIFICATION
        self.industry_code = "541511"                 # NAICS code (see table below)
        self.tax_id = "12-3456789"                   # EIN format
        
        # 💰 FINANCIAL DATA (USD) - Critical for loan approval
        self.financials_annual_revenue = 50000000     # $50M annual revenue
        self.financials_net_income = 7500000          # $7.5M net income
        self.financials_assets_total = 40000000       # $40M total assets
        self.financials_liabilities_total = 15000000  # $15M liabilities
        
        # 🌱 ESG CONFIGURATION
        self.carbon_emissions_tons_co2e = 8500        # Annual CO2 emissions
        self.ESG_impact_ratio = "0.75"                # ESG commitment (0-1)
        self.esg_certifications = "B-Corp,ISO14001"   # Comma-separated certs
        self.esg_reporting_url = "https://yourcompany.com/esg-report"
        
        # 📋 REGULATORY COMPLIANCE
        self.regulatory_context_jurisdiction = "SEC,FINRA"
        self.regulatory_context_required_disclosures = "10-K Filing,SOX Compliance"
        
        # 📊 CREDIT INFORMATION
        self.credit_report_ref = "DN-12345678"        # D&B reference
```

#### Method 2: Use Sample Company Templates

The system includes 6 pre-built company profiles in `code/test/company_configs/`:
1. **Healthcare Services** (`healthcare_services_config.py`)
   - Sunshine Medical Group - Healthcare provider
   - Revenue: $125M, ESG-focused, HIPAA compliant

2. **Manufacturing** (`manufacturing_company_config.py`)
   - Industrial manufacturing with equipment financing needs
   - Revenue: $89M, moderate ESG, heavy asset base

3. **Renewable Energy** (`renewable_energy_mnc_config.py`)
   - Clean energy multinational corporation
   - Revenue: $2.1B, exceptional ESG scores, global operations

4. **Retail Chain** (`retail_chain_config.py`)
   - Multi-location retail business
   - Revenue: $156M, consumer-facing, seasonal patterns

5. **Startup Tech** (`startup_tech_config.py`)
   - Early-stage technology company
   - Revenue: $8M, high growth, limited assets

6. **Technology Services** (`technology_services_config.py`)
   - Established tech services provider
   - Revenue: $45M, digital-first, strong IP portfolio

**To use a sample configuration:**

```bash
# Copy desired config to host_agent_adk/company_config.py
cp code/test/company_configs/technology_services_config.py code/src/host_agent_adk/company_config.py
```

#### Method 3: Create Custom Company Profile

```python
# Create new file: my_custom_company.py
import uuid
from datetime import datetime
import secrets

class CorporateConfig:
    def __init__(self):
        # Start with template above and customize:
        
        # Example: Logistics Company
        self.sender_name = "GlobalLogistics Express LLC"
        self.industry_code = "484110"  # General Freight Trucking
        self.financials_annual_revenue = 75000000
        self.carbon_emissions_tons_co2e = 25000  # Higher for transportation
        self.esg_certifications = "SmartWay,ISO14001"
        
        # ... rest of configuration
```

### 📊 Industry Codes Reference

| Industry | NAICS Code | Risk Level | Typical Revenue Range |
|----------|------------|------------|----------------------|
| Software Development | 541511 | Low | $10M - $500M |
| Healthcare Services | 621111 | Low | $25M - $200M |
| Manufacturing | 336000 | Medium | $50M - $1B |
| Retail Trade | 452000 | Medium | $20M - $300M |
| Transportation | 484110 | Medium | $30M - $150M |
| Oil & Gas | 211111 | High | $100M - $5B |
| Real Estate | 531000 | High | $15M - $100M |

### 🌱 ESG Certification Options

```python
# Combine certifications with commas:
self.esg_certifications = "B-Corp,ISO14001,SBTI,LEED,ENERGY STAR,Carbon Neutral"
```

**Available Certifications:**
- **B-Corp**: Certified B Corporation (40 points)
- **ISO14001**: Environmental Management (25 points) 
- **SBTI**: Science Based Targets Initiative (25 points)
- **LEED**: Green Building Certification (15 points)
- **ENERGY STAR**: Energy Efficiency (15 points)
- **Carbon Neutral**: Net-zero emissions (20 points)

---

## 🛠️ Developer Deep Dive

### Project Structure Walkthrough
🔬 Technical Implementation
```
a2a_consumer_bank/
├── code/src/                          # Main application code
│   ├── bank_agent_[1-5]_adk/         # Individual bank microservices
│   │   ├── main.py                   # Uvicorn server entry point
│   │   ├── agent.py                  # ADK agent configuration & workflow
│   │   ├── agent_executor.py         # Request processing pipeline
│   │   ├── bank_policy_tools.py      # Core banking business logic
│   │   └── wfap_protocol.py         # Data models & protocol
│   ├── host_agent_adk/              # Consumer agent & web interface
│   │   ├── start_custom_ui.py       # Flask web server launcher
│   │   ├── web_server.py           # Flask app & API endpoints
│   │   ├── agent.py                # Consumer agent orchestration
│   │   ├── company_config.py       # Company profile configuration
│   │   ├── index.html              # React-like web interface
│   │   ├── script.js               # Frontend JavaScript
│   │   └── styles.css              # Modern CSS styling
│   └── test/                       # Sample data & configurations
├── artifacts/arch/                 # Architecture documentation
└── README.md                      # This file
```

### Key Development Files

#### 🎯 **Banking Logic** (`bank_policy_tools.py`)
Contains the core financial algorithms:
- `perform_initial_risk_assessment()` - Eligibility screening
- `calculate_interest_rate_and_offer()` - Rate calculation with ESG discounts
- `calculate_final_approved_amount()` - Dynamic lending ratio model
- `calculate_approved_repayment_duration()` - Term optimization
- `generate_loan_offer_json()` - Final offer assembly

#### 🌐 **Web Interface** (`index.html` + `script.js`)
Modern single-page application featuring:
- Real-time chat interface with AI assistant
- Company profile management
- Multi-bank offer comparison
- Interactive negotiation workflows
- Responsive design with dark/light themes

#### 🤖 **Agent Workflows** (`agent.py`)
Each bank agent follows a structured workflow:
1. Initial risk assessment
2. Financial analysis & scoring
3. ESG evaluation & discount calculation
4. Offer generation with digital signatures
5. Negotiation handling

---

## 🔬 Technical Implementation

### Agent Development Kit Integration

```python
# Example: Creating a bank agent
from google.adk.agents import Agent
from tachyon_adk_client import TachyonAdkClient

def create_agent() -> Agent:
    return Agent(
        model=TachyonAdkClient(model_name="gemini-2.5-flash"),
        name="bank_loan_processing_agent",
        description="AI agent for credit line processing",
        tools=[
            perform_initial_risk_assessment,
            calculate_interest_rate_and_offer,
            # ... other banking tools
        ]
    )
```

### WFAP Protocol Implementation

The Wells Fargo Agent Protocol (WFAP) defines structured message exchange:

```python
# Intent Packet (Consumer → Bank)
{
  "intent_id": "uuid-string",
  "sender_name": "Company Name",
  "financials_annual_revenue": 50000000,
  "esg_certifications": "B-Corp,ISO14001",
  # ... other fields
}

# Offer Packet (Bank → Consumer)
{
  "offer_id": "uuid-string", 
  "amount_approved": 500000,
  "interest_rate_annual": 7.25,
  "esg_impact_summary": "Company demonstrates strong...",
  # ... other fields
}
```

### ESG Scoring Algorithm

```python
# Carbon Performance (70% weight)
carbon_intensity = emissions / (revenue / 1_000_000)
industry_benchmark = get_industry_benchmark(naics_code)
carbon_performance = calculate_performance_vs_benchmark(carbon_intensity, industry_benchmark)

# Qualitative ESG (30% weight)  
certification_score = sum(CERTIFICATION_POINTS[cert] for cert in certifications)

# Final ESG Score & Interest Discount
esg_score = (carbon_performance * 0.7) + (certification_score * 0.3)
interest_discount = calculate_esg_discount(esg_score)  # 0-0.75%
```

---

## 🧪 Testing & Development Workflows

### Health Checks

```bash
# Verify all bank agents are running
curl http://localhost:10002/.well-known/agent-card.json  # CloudTrust
curl http://localhost:10003/.well-known/agent-card.json  # Finovate  
curl http://localhost:10004/.well-known/agent-card.json  # Zentra
curl http://localhost:10005/.well-known/agent-card.json  # NexVault
curl http://localhost:10006/.well-known/agent-card.json  # Byte Bank
```

### Sample Credit Requests

The system includes realistic credit scenarios in `code/test/credit_requests/`:
- **CloudScale AI** - AI/ML startup seeking working capital
- **GreenPower Global** - Renewable energy expansion financing  
- **Midwest Steel** - Manufacturing equipment loans
- **Pacific Coast** - Seasonal business credit lines
- **Sunshine Medical** - Healthcare facility improvements

### Running Tests

```bash
cd code/src
pytest                           # Run all tests
pytest -v                       # Verbose output
pytest --asyncio-mode=auto      # Async test support
```

### Code Formatting

```bash
black .                         # Format all Python code
black bank_agent_1_adk/         # Format specific module
```

---

## 🔧 Extending the System

### Adding New Bank Agents

1. **Copy existing agent structure:**    
```bash
cp -r bank_agent_1_adk/ bank_agent_6_adk/
```

2. **Update configuration:**
```python
# In main.py
port = 10007  # New port
agent_card = AgentCard(name="NewBank Agent", ...)
```

3. **Customize banking policies:**
```python
# In bank_policy_tools.py - adjust risk thresholds, rates, etc.
MIN_ANNUAL_REVENUE = 10_000_000  # Custom minimum
BASE_INTEREST_RATE = 6.8         # Custom base rate
```

4. **Update startup scripts:**
```bash
# Add to start_banking_system.bat
echo Starting Bank Agent 6...
start "Bank Agent 6" cmd /k "python -m bank_agent_6_adk.main"    
```

### ESG Enhancements

```python
# Add new certification types
CERTIFICATION_POINTS = {
    "B-Corp": 40,
    "ISO14001": 25,
    "NEW_GREEN_CERT": 30,  # Your custom certification
    # ...
}

# Update industry carbon benchmarks
INDUSTRY_BENCHMARKS = {
    "999999": 150,  # New NAICS code
    # ...
}
```

### Custom Risk Models

```python
# bank_policy_tools.py - modify risk assessment
def perform_initial_risk_assessment(data):
    # Add custom industry restrictions
    prohibited_industries = ["720000", "713000"]  # Gaming, entertainment
    
    # Custom geographic restrictions
    high_risk_jurisdictions = ["certain-countries"]
    
    # Your custom logic here
    return "PASS" or "FAIL"
```

---

## 🌐 Web Interface Customization

### Frontend Architecture

The web interface uses vanilla JavaScript with modern patterns:

```javascript
// script.js - Main application class
class ChatApp {
    constructor() {
        this.settings = { autoScroll: true, sound: true, theme: 'auto' };
        this.elements = {}; // DOM element cache
    }
    
    async sendMessage(message) {
        // Handle user interactions
    }
    
    displayOffers(offers) {
        // Render loan comparison table
    }
}
```

### Styling System

```css
/* styles.css - CSS custom properties for theming */
:root {
    --primary-color: #2563eb;
    --success-color: #059669;
    --warning-color: #d97706;
    --error-color: #dc2626;
    /* ... extensive design system */
}
```

### Adding Custom Features

1. **New API Endpoints:**
```python
# web_server.py
@app.route('/api/custom-endpoint', methods=['POST'])
def custom_endpoint():
    # Your custom backend logic
    return jsonify({"status": "success"})
```

2. **Frontend Components:**
```javascript
// script.js - Add new UI functions
function showCustomModal(data) {
    // Your custom UI logic
}
```

---

## 📊 Banking Policies & Risk Framework

### Risk Classification Levels

| Risk Level | Industries | Min Revenue | Max LTV | Base Rate |
|------------|------------|-------------|---------|-----------|
| **Low** | Tech, Healthcare, Professional | $5M+ | 85% | 6.5% |
| **Medium** | Manufacturing, Retail, Construction | $10M+ | 75% | 7.0% |
| **High** | Oil & Gas, Mining, Real Estate | $25M+ | 65% | 8.0% |
| **Prohibited** | Crypto, Gaming, Adult, Cannabis | N/A | N/A | N/A |

### Interest Rate Calculation

```
Final Rate = Base Rate + Risk Premium - ESG Discount

Risk Premium = 0.5% to 6.0% (based on financial health)
ESG Discount = 0.0% to 0.75% (based on ESG score)
```

### Credit Limits

```python
# Dynamic lending ratio model
approved_amount = min(
    requested_amount,
    annual_revenue * lending_ratio,  # 10-20% of revenue
    policy_maximum                   # $5M max per bank
)
```

---

## 🚨 Troubleshooting Guide

### Common Issues

#### Port Conflicts
```bash
# Find processes using banking ports
netstat -ano | findstr :10002
taskkill /PID <process_id> /F
```

#### Missing Dependencies
```bash
# Reinstall with fresh environment
pip install --upgrade --force-reinstall -r requirements.txt
```

#### Invalid API Key
```bash
# Check API key
echo $API_KEY
```

#### Debugging
```bash
# Enable debug logging
python -m bank_agent_1_adk.main --log-level DEBUG
```

---

## 🔒 Security & Compliance Notes

### Authentication & Authorization
- All API requests include cryptographic signatures
- OAuth 2.0 for agent authentication

### Data Privacy
- No persistent storage of sensitive financial data
- In-memory session management
- HTTPS recommended for production

### Regulatory Compliance
- Built-in industry eligibility checks
- Customizable jurisdiction-specific validation
- AML screening capabilities (framework provided)

### Infrastructure Requirements

```yaml
# Recommended production setup
Bank Agents:
  - CPU: 2+ cores per agent
  - Memory: 4GB+ per agent  
  - Network: Low latency between agents
  
Consumer Interface:
  - CPU: 4+ cores
  - Memory: 8GB+
  - Storage: 20GB+ for logs
  
Load Balancing:
  - Reverse proxy (nginx/Apache)
  - SSL/TLS termination
  - Rate limiting
```

### Environment Variables

```bash
# Production .env file
USE_API_GATEWAY=true
APIGEE_URL=https://api.wellsfargo.com
BASE_URL=https://your-base-url.com
USE_CASE_ID=your_use_case_id
API_KEY=your_api_key
CONSUMER_KEY=your_consumer_key
CONSUMER_SECRET=your_consumer_secret
CERTS_PATH=./certs
LOG_LEVEL=INFO
FLASK_ENV=production
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
RATE_LIMIT_PER_MINUTE=60
```

### Monitoring & Observability

```python
# Add to each agent
import logging
import prometheus_client

# Metrics collection
REQUEST_COUNT = Counter('banking_requests_total')
RESPONSE_TIME = Histogram('banking_response_seconds')

# Health check endpoint
@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

---

## 🤝 Contributing & Development Guidelines

### Code Standards

```bash
# Before committing
black .                    # Format code
pytest                    # Run tests  
mypy bank_agent_1_adk/    # Type checking
```

### Git Workflow

```bash
# Feature development
git checkout -b feature/new-bank-integration
git commit -m "feat: add XYZ Bank agent with custom policies"
git push origin feature/new-bank-integration
```

### Documentation Updates

When adding features:
1. Update relevant docstrings
2. Add examples to this README
3. Update API documentation
4. Include test cases

---

## 📚 Additional Resources

### Architecture Documents
- `artifacts/arch/Software_Architecture_Document_A2A_Consumer_Bank.md` - Comprehensive system design
- `artifacts/arch/WFAP_Intent_Schema.json` - Protocol message schemas
- `artifacts/arch/WFAP_Response_Schema.json` - Response format specifications

### External References
- [Google ADK Documentation](https://developers.google.com/agent-development-kit)
- [A2A Protocol Specification](https://a2a.dev/)
- [NAICS Industry Codes](https://www.census.gov/naics/)
- [ESG Reporting Standards](https://www.sasb.org/)

---

## ⚖️ Legal & License

**Important Notice:** This is a proof-of-concept system for demonstration and educational purposes. For production deployment in financial services:

- Conduct comprehensive security audits
- Implement full regulatory compliance measures
- Obtain necessary financial services licenses
- Perform extensive testing and validation
- Implement proper data governance and privacy controls

**Disclaimer:** This software is provided "as-is" for demonstration purposes. Not suitable for production use without proper security reviews and regulatory compliance verification.

---

*Built with ❤️ by the CreditAvengers team using Google ADK & A2A Protocol Framework*

**System Version:** 1.0.0  
**Last Updated:** September 2025  
**Compatible With:** Python 3.8+, Google ADK 1.0+