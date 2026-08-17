import json
import re
import secrets
import uuid
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import Customer, PaymentPromise

app = FastAPI()

# In-memory store: session_id -> customer_id
# Acceptable for this prototype.
verification_sessions = {}


class VerifyRequest(BaseModel):
    customer_id: str
    verification_code: str


class LogPromiseRequest(BaseModel):
    customer_id: str
    amount: int
    promised_date: date


class SendPaymentLinkRequest(BaseModel):
    customer_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    customer = (
        db.query(Customer)
        .filter(Customer.customer_id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "phone": customer.phone,
        "loan_type": customer.loan_type,
        "overdue_amount": customer.overdue_amount,
        "days_past_due": customer.days_past_due,
        "payment_status": customer.payment_status,
    }


# ============================================================
# IDENTIFIER NORMALIZATION
# ============================================================

def _normalize_identifier(value: str) -> str:
    """
    Normalize identifiers for comparison only.

    Removes spaces, hyphens, punctuation, etc.
    Converts everything to lowercase.

    Examples:
        CUST001
        CUST 001
        CUST-001
        C.U.S.T. 001

    All become:
        cust001
    """

    if value is None:
        return ""

    return re.sub(
        r'[^a-zA-Z0-9]',
        '',
        value
    ).lower()


def _get_customer_by_id(
    customer_id: str,
    db: Session
):
    """
    Find a customer using a normalized customer ID.

    The database value is never modified.
    This is only for tolerant comparison of STT output.
    """

    normalized_id = _normalize_identifier(customer_id)

    all_customers = db.query(Customer).all()

    return next(
        (
            customer
            for customer in all_customers
            if _normalize_identifier(customer.customer_id)
            == normalized_id
        ),
        None,
    )


# ============================================================
# CORE LOGIC
# ============================================================

def _verify_customer_logic(
    customer_id: str,
    verification_code: str,
    db: Session
):
    customer = _get_customer_by_id(
        customer_id,
        db
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    is_verified = (
        _normalize_identifier(customer.verification_code)
        == _normalize_identifier(verification_code)
    )

    if not is_verified:
        return {
            "verified": False
        }

    session_id = secrets.token_urlsafe(16)

    # IMPORTANT:
    # Store the real/canonical customer ID from the database.
    verification_sessions[session_id] = customer.customer_id

    return {
        "verified": True,
        "verification_session_id": session_id
    }


def _check_session(
    verification_session_id: str,
    customer_id: str
):
    """
    Verify that the session exists and belongs
    to the requested customer.
    """

    session_customer_id = verification_sessions.get(
        verification_session_id
    )

    if session_customer_id is None:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing verification session"
        )

    # Compare normalized IDs so STT formatting
    # does not break an already-valid session.
    if (
        _normalize_identifier(session_customer_id)
        != _normalize_identifier(customer_id)
    ):
        raise HTTPException(
            status_code=403,
            detail="Session does not belong to this customer"
        )


def _get_account_details_logic(
    customer_id: str,
    verification_session_id: str,
    db: Session
):
    # NORMALIZED lookup
    customer = _get_customer_by_id(
        customer_id,
        db
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # Use the REAL database customer ID for authorization.
    _check_session(
        verification_session_id,
        customer.customer_id
    )

    return {
        "customer_id": customer.customer_id,
        "loan_type": customer.loan_type,
        "overdue_amount": customer.overdue_amount,
        "days_past_due": customer.days_past_due,
        "payment_status": customer.payment_status,
    }


def _log_promise_to_pay_logic(
    customer_id: str,
    amount: int,
    promised_date: date,
    verification_session_id: str,
    db: Session
):
    # NORMALIZED lookup
    customer = _get_customer_by_id(
        customer_id,
        db
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # Use the REAL database customer ID.
    _check_session(
        verification_session_id,
        customer.customer_id
    )

    promise_id = str(uuid.uuid4())

    promise = PaymentPromise(
        promise_id=promise_id,
        customer_id=customer.customer_id,
        amount=amount,
        promised_date=promised_date.isoformat(),
        status="PROMISED",
    )

    db.add(promise)
    db.commit()

    return {
        "success": True,
        "promise_id": promise_id,
        "customer_id": customer.customer_id,
        "amount": amount,
        "promised_date": promised_date.isoformat(),
        "status": "PROMISED",
    }


def _send_payment_link_logic(
    customer_id: str,
    verification_session_id: str,
    db: Session
):
    # NORMALIZED lookup
    customer = _get_customer_by_id(
        customer_id,
        db
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # Use the REAL database customer ID.
    _check_session(
        verification_session_id,
        customer.customer_id
    )

    link_id = secrets.token_urlsafe(8)

    payment_link = (
        f"https://example.test/pay/{link_id}"
    )

    return {
        "success": True,
        "customer_id": customer.customer_id,
        "payment_link": payment_link,
    }


# ============================================================
# EXISTING REST ENDPOINTS
# ============================================================

@app.post("/verify-customer")
def verify_customer(
    request: VerifyRequest,
    db: Session = Depends(get_db)
):
    return _verify_customer_logic(
        request.customer_id,
        request.verification_code,
        db
    )


@app.get("/account-details/{customer_id}")
def get_account_details(
    customer_id: str,
    verification_session_id: str,
    db: Session = Depends(get_db)
):
    return _get_account_details_logic(
        customer_id,
        verification_session_id,
        db
    )


@app.post("/log-promise-to-pay")
def log_promise_to_pay(
    request: LogPromiseRequest,
    verification_session_id: str,
    db: Session = Depends(get_db)
):
    return _log_promise_to_pay_logic(
        request.customer_id,
        request.amount,
        request.promised_date,
        verification_session_id,
        db
    )


@app.post("/send-payment-link")
def send_payment_link(
    request: SendPaymentLinkRequest,
    verification_session_id: str,
    db: Session = Depends(get_db)
):
    return _send_payment_link_logic(
        request.customer_id,
        verification_session_id,
        db
    )


# ============================================================
# VAPI CUSTOM TOOL WEBHOOK
# ============================================================

@app.post("/vapi/tools")
async def vapi_tools(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.json()

    tool_calls = (
        body
        .get("message", {})
        .get("toolCallList", [])
    )

    results = []

    for call in tool_calls:

        tool_call_id = call.get("id")

        function = call.get(
            "function",
            {}
        )

        tool_name = (
            call.get("name")
            or function.get("name")
        )

        arguments = (
            call.get("arguments")
            or call.get("parameters")
            or function.get("arguments")
            or function.get("parameters")
            or {}
        )

        # Vapi may send arguments as a JSON string.
        if isinstance(arguments, str):

            try:
                arguments = json.loads(arguments)

            except json.JSONDecodeError:
                arguments = {}

        try:

            # ----------------------------------------------------
            # VERIFY CUSTOMER
            # ----------------------------------------------------

            if tool_name == "verify_customer":

                result = _verify_customer_logic(
                    customer_id=arguments.get(
                        "customer_id"
                    ),
                    verification_code=arguments.get(
                        "verification_code"
                    ),
                    db=db
                )

            # ----------------------------------------------------
            # GET ACCOUNT DETAILS
            # ----------------------------------------------------

            elif tool_name == "get_account_details":

                result = _get_account_details_logic(
                    customer_id=arguments.get(
                        "customer_id"
                    ),
                    verification_session_id=arguments.get(
                        "verification_session_id"
                    ),
                    db=db
                )

            # ----------------------------------------------------
            # LOG PROMISE TO PAY
            # ----------------------------------------------------

            elif tool_name == "log_promise_to_pay":

                promised_date_value = arguments.get(
                    "promised_date"
                )

                promised_date = date.fromisoformat(
                    promised_date_value
                )

                result = _log_promise_to_pay_logic(
                    customer_id=arguments.get(
                        "customer_id"
                    ),
                    amount=arguments.get(
                        "amount"
                    ),
                    promised_date=promised_date,
                    verification_session_id=arguments.get(
                        "verification_session_id"
                    ),
                    db=db
                )

            # ----------------------------------------------------
            # SEND PAYMENT LINK
            # ----------------------------------------------------

            elif tool_name == "send_payment_link":

                result = _send_payment_link_logic(
                    customer_id=arguments.get(
                        "customer_id"
                    ),
                    verification_session_id=arguments.get(
                        "verification_session_id"
                    ),
                    db=db
                )

            # ----------------------------------------------------
            # UNKNOWN TOOL
            # ----------------------------------------------------

            else:

                result = {
                    "error": f"Unknown tool: {tool_name}"
                }

        except HTTPException as e:

            result = {
                "error": e.detail,
                "status_code": e.status_code
            }

        except Exception as e:

            result = {
                "error": str(e),
                "status_code": 400
            }

        results.append({
            "toolCallId": tool_call_id,
            "result": json.dumps(result)
        })

    return {
        "results": results
    }