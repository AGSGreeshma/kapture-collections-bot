@"
# Kapture Collections Voicebot

An AI-powered collections voicebot prototype built with **Vapi, FastAPI, SQLAlchemy, and SQLite**.

The system handles customer verification, protected account access, payment commitments, and payment-link requests while enforcing verification at the backend level.

---

## Features

- Customer identity verification
- Backend-enforced verification sessions
- Protected account/debt information
- Promise-to-pay logging
- Payment-link generation
- Vapi Custom Tool integration
- REST APIs for backend testing
- SQLite database for prototype persistence
- Speech-to-text tolerant customer ID and verification-code matching
- English, Hindi, and Hinglish conversational support through Vapi configuration

---

## Architecture

    Customer
        |
        v
      Vapi
        |
        v
      ngrok
        |
        v
     FastAPI
        |
        +-----------------------------+
        |                             |
        v                             v
   Vapi Tool Dispatcher           SQLite
        |
        +-----------------------------+
        |
        +-- verify_customer
        |
        +-- get_account_details
        |
        +-- log_promise_to_pay
        |
        +-- send_payment_link

---

## Tech Stack

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- Pydantic
- Vapi
- ngrok
- Git / GitHub

---

## Project Structure

    kapture-collections-bot/
    |
    +-- main.py
    +-- database.py
    +-- models.py
    +-- seed.py
    +-- README.md
    +-- .gitignore
    |
    +-- venv/

> `venv/` and the SQLite database are excluded from Git using `.gitignore`.

---

## Security Design

Customer account information is protected by a backend-enforced verification flow.

    Customer
        |
        v
    verify_customer
        |
        +-- Invalid -> verified: false
        |
        +-- Valid
              |
              v
      verification_session_id
              |
              v
       Protected tools

The LLM is not trusted to remember whether a customer was verified.

The backend checks the verification session before allowing protected operations.

---

## Backend Tools

### 1. verify_customer

Verifies the caller using:

- `customer_id`
- `verification_code`

Successful verification creates a temporary verification session.

Example:

    {
      "verified": true,
      "verification_session_id": "..."
    }

---

### 2. get_account_details

Requires:

- `customer_id`
- `verification_session_id`

Returns the verified customer's:

- loan type
- overdue amount
- days past due
- payment status

Example:

    {
      "customer_id": "CUST001",
      "loan_type": "Personal Loan",
      "overdue_amount": 8499,
      "days_past_due": 12,
      "payment_status": "OVERDUE"
    }

---

### 3. log_promise_to_pay

Records a confirmed commitment from the customer to pay a specific amount by a specific date.

Required information:

- `customer_id`
- `amount`
- `promised_date`
- `verification_session_id`

Example:

    {
      "customer_id": "CUST001",
      "amount": 5000,
      "promised_date": "2026-08-21"
    }

---

### 4. send_payment_link

Generates a payment link for a verified customer who wants to make a payment.

Required information:

- `customer_id`
- `verification_session_id`

Example result:

    {
      "success": true,
      "customer_id": "CUST001",
      "payment_link": "https://example.test/pay/..."
    }

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/customers/{customer_id}` | Retrieve prototype customer record |
| POST | `/verify-customer` | Verify customer |
| GET | `/account-details/{customer_id}` | Retrieve protected account details |
| POST | `/log-promise-to-pay` | Record payment commitment |
| POST | `/send-payment-link` | Generate payment link |
| POST | `/vapi/tools` | Vapi Custom Tool dispatcher |

---

## Local Setup

### 1. Create virtual environment

    python -m venv venv

### 2. Activate the environment

Windows PowerShell:

    venv\Scripts\activate

### 3. Install dependencies

    pip install fastapi uvicorn sqlalchemy

### 4. Create and seed the database

    python seed.py

### 5. Start FastAPI

    uvicorn main:app --reload

The API will be available at:

    http://127.0.0.1:8000

Interactive API documentation:

    http://127.0.0.1:8000/docs

---

## Vapi Integration

The Vapi Custom Tools communicate with the FastAPI backend through an ngrok HTTPS tunnel.

    Vapi
      |
      v
    https://<ngrok-domain>/vapi/tools
      |
      v
    FastAPI

The following Vapi Custom Tools are configured:

- `verify_customer`
- `get_account_details`
- `log_promise_to_pay`
- `send_payment_link`

---

## Testing

The backend was tested using FastAPI's interactive `/docs` interface.

Test cases include:

- Successful customer verification
- Failed customer verification
- Unknown customer
- Valid verification session
- Invalid verification session
- Cross-customer session access
- Successful promise-to-pay creation
- Invalid promise-to-pay session
- Cross-customer promise attempt
- Payment-link generation

The voicebot was also tested through Vapi using a natural spoken verification flow.

---

## Voice Interaction

The assistant is designed to:

1. Introduce itself
2. Confirm the intended customer
3. Verify the customer before disclosure
4. Retrieve account details after successful verification
5. Understand payment intent
6. Record a specific promise-to-pay when appropriate
7. Provide a payment link when requested
8. Handle English, Hindi, and Hinglish conversationally

The assistant should never disclose account information to an unverified caller.

---

## Prototype Notes

This project is intentionally designed as a lightweight prototype.

Verification sessions are stored in an in-memory Python dictionary.

For a production deployment, this would be replaced with a persistent or distributed session store such as Redis with appropriate expiration and security controls.

The payment URL currently uses a mock domain:

    https://example.test/pay/...

It represents a payment-link integration point rather than a real payment gateway.

The customer data used in the prototype is synthetic.

---

## Future Improvements

- Production-grade authentication
- Redis-based session storage with TTL
- Real payment gateway integration
- Real SMS/payment-link delivery
- Persistent call disposition logging
- Production database
- Alembic database migrations
- Better call analytics and monitoring
- Production-grade multilingual speech handling
- Production secrets management

---

## Project

**Kapture Collections Voicebot**

Built as a prototype demonstrating:

**Voice AI + Backend APIs + Database + Authentication/Authorization + Payment Workflow**
"@ | Out-File -Encoding utf8 README.md
