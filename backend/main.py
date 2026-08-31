from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from types import SimpleNamespace
from pathlib import Path

from backend.database import Base, engine, SessionLocal
from backend import models
from backend.recovery import get_recovery_recommendation
from backend.ai_agent import diagnose_payment
from backend.context_builder import build_payment_context
from backend.policy_engine import evaluate_policy
from backend.recovery_executor import execute_recovery
from backend.razorpay_client import create_test_order
from backend.metrics import calculate_metrics


# =========================================================
# DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(title="RecoverAI")


# =========================================================
# DASHBOARD FRONTEND
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"

app.mount(
    "/ui",
    StaticFiles(directory=str(DASHBOARD_DIR), html=True),
    name="dashboard"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "RecoverAI is running!"
    }


# =========================================================
# FAILED PAYMENTS
# =========================================================

@app.get("/payments/failed")
def get_failed_payments(
    db: Session = Depends(get_db)
):

    payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "failed")
        .all()
    )

    return payments


# =========================================================
# RECOVERY TEST
# =========================================================

@app.get("/recovery/test")
def test_recovery(
    failure_reason: str = ""
):

    test_payment = SimpleNamespace(
        failure_reason=failure_reason
    )

    return get_recovery_recommendation(
        test_payment
    )


# =========================================================
# RECOVERY RECOMMENDATION
# =========================================================

@app.get("/recovery/{payment_id}")
def get_recovery(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:

        return {
            "error": "Payment not found"
        }

    return get_recovery_recommendation(
        payment
    )


# =========================================================
# AI DIAGNOSIS
# =========================================================

@app.get("/ai-diagnosis/{payment_id}")
def ai_diagnosis(
    payment_id: int,
    db: Session = Depends(get_db)
):

    context = build_payment_context(
        payment_id,
        db
    )

    if not context:

        return {
            "error": "Payment not found"
        }

    return diagnose_payment(
        context
    )


# =========================================================
# POLICY & SAFETY ENGINE
# =========================================================

@app.get("/policy/{payment_id}")
def check_policy(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:

        return {
            "error": "Payment not found"
        }

    context = build_payment_context(
        payment_id,
        db
    )

    if not context:

        return {
            "error": "Payment context could not be built"
        }

    diagnosis = diagnose_payment(
        context
    )

    policy_result = evaluate_policy(
        payment=payment,
        diagnosis=diagnosis
    )

    return policy_result


# =========================================================
# EXECUTE RECOVERY
# =========================================================

@app.get("/execute-recovery/{payment_id}")
def execute_payment_recovery(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:

        return {
            "error": "Payment not found"
        }

    context = build_payment_context(
        payment_id,
        db
    )

    if not context:

        return {
            "error": "Payment context could not be built"
        }

    # -----------------------------------------------------
    # AI diagnosis
    # -----------------------------------------------------

    diagnosis = diagnose_payment(
        context
    )

    # -----------------------------------------------------
    # Policy evaluation
    # -----------------------------------------------------

    policy_result = evaluate_policy(
        payment=payment,
        diagnosis=diagnosis
    )

    # -----------------------------------------------------
    # Execute ONLY approved action
    # -----------------------------------------------------

    execution_result = execute_recovery(
        payment=payment,
        policy_result=policy_result,
        db=db
    )

    return {

        "payment_id": payment_id,

        "diagnosis": diagnosis,

        "policy": policy_result,

        "execution": execution_result

    }


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Get records
    # -----------------------------------------------------

    payments = (
        db.query(models.Payment)
        .order_by(models.Payment.id)
        .all()
    )

    attempts = (
        db.query(models.PaymentAttempt)
        .order_by(models.PaymentAttempt.id)
        .all()
    )

    # -----------------------------------------------------
    # PAYMENT STATISTICS
    # -----------------------------------------------------

    total_payments = len(payments)

    failed_payments = len([
        payment
        for payment in payments
        if payment.status == "failed"
    ])

    successful_payments = len([
        payment
        for payment in payments
        if payment.status in [
            "success",
            "captured",
            "paid"
        ]
    ])

    # -----------------------------------------------------
    # RECOVERY STATISTICS
    # -----------------------------------------------------

    executed_actions = len([
        attempt
        for attempt in attempts
        if attempt.status in [
            "retry_scheduled",
            "waiting_for_funds",
            "customer_action_required",
            "bank_contact_required",
            "success"
        ]
    ])

    blocked_actions = len([
        attempt
        for attempt in attempts
        if attempt.status in [
            "retry_blocked",
            "blocked"
        ]
    ])

    human_review_cases = len([
        attempt
        for attempt in attempts
        if attempt.status in [
            "human_review_required",
            "needs_human"
        ]
    ])

    # -----------------------------------------------------
    # CONFIRMED SUCCESSFUL RECOVERIES
    # -----------------------------------------------------

    confirmed_successful_payments = len([
        attempt
        for attempt in attempts
        if attempt.status == "success"
    ])

    # -----------------------------------------------------
    # CONFIRMED RECOVERY RATE
    #
    # Numerator:
    # confirmed successful recovery attempts
    #
    # Denominator:
    # failed payments
    # -----------------------------------------------------

    confirmed_payment_recovery_rate_percent = 0.0

    if failed_payments > 0:

        confirmed_payment_recovery_rate_percent = round(
            (
                confirmed_successful_payments
                / failed_payments
            ) * 100,
            2
        )

    # -----------------------------------------------------
    # PAYMENT DATA
    # -----------------------------------------------------

    payment_data = [

        {
            "payment_id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "failure_reason": payment.failure_reason
        }

        for payment in payments
    ]

    # -----------------------------------------------------
    # PAYMENT ATTEMPT DATA
    # -----------------------------------------------------

    attempt_data = [

        {
            "attempt_id": attempt.id,
            "payment_id": attempt.payment_id,
            "status": attempt.status,
            "failure_reason": attempt.failure_reason
        }

        for attempt in attempts
    ]

    # -----------------------------------------------------
    # FINAL DASHBOARD RESPONSE
    # -----------------------------------------------------

    return {

        "statistics": {

            "total_payments":
                total_payments,

            "failed_payments":
                failed_payments,

            "successful_payments":
                successful_payments,

            "executed_actions":
                executed_actions,

            "blocked_actions":
                blocked_actions,

            "human_review_cases":
                human_review_cases,

            "confirmed_successful_payments":
                confirmed_successful_payments,

            "confirmed_payment_recovery_rate_percent":
                confirmed_payment_recovery_rate_percent
        },

        "payments":
            payment_data,

        "payment_attempts":
            attempt_data
    }


# =========================================================
# RAZORPAY TEST MODE ORDER
# =========================================================

@app.post("/razorpay/test-order")
def create_razorpay_test_order(
    db: Session = Depends(get_db)
):

    try:

        order = create_test_order(
            100
        )

        return {

            "status": "success",

            "message":
                "Razorpay Test Mode order created.",

            "order_id":
                order["id"],

            "amount":
                order["amount"],

            "currency":
                order["currency"]
        }

    except Exception as e:

        return {

            "status": "failed",

            "message":
                "Unable to create Razorpay test order.",

            "error":
                str(e)
        }


# =========================================================
# METRICS & EVALUATION
# =========================================================

@app.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db)
):

    return calculate_metrics(db)