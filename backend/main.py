from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from types import SimpleNamespace

from backend.database import Base, engine, SessionLocal
from backend import models
from backend.recovery import get_recovery_recommendation
from backend.ai_agent import diagnose_payment
from backend.context_builder import build_payment_context
from backend.policy_engine import evaluate_policy
from backend.recovery_executor import execute_recovery
from backend.razorpay_client import create_test_order
from backend.metrics import calculate_metrics
from pathlib import Path

# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(title="RecoverAI")

# Dashboard frontend
BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"

# Serve the frontend dashboard
app.mount(
    "/ui",
    StaticFiles(directory="dashboard", html=True),
    name="dashboard"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Home Endpoint
# ---------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "RecoverAI is running!"
    }


# ---------------------------------------------------------
# Get Failed Payments
# ---------------------------------------------------------

@app.get("/payments/failed")
def get_failed_payments(db: Session = Depends(get_db)):
    payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "failed")
        .all()
    )

    return payments


# ---------------------------------------------------------
# Recovery Test Endpoint
# ---------------------------------------------------------

@app.get("/recovery/test")
def test_recovery(failure_reason: str = ""):
    test_payment = SimpleNamespace(
        failure_reason=failure_reason
    )

    return get_recovery_recommendation(test_payment)


# ---------------------------------------------------------
# Recovery Recommendation
# ---------------------------------------------------------

@app.get("/recovery/{payment_id}")
def get_recovery(payment_id: int, db: Session = Depends(get_db)):

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:
        return {
            "error": "Payment not found"
        }

    return get_recovery_recommendation(payment)


# ---------------------------------------------------------
# AI Diagnosis
# ---------------------------------------------------------

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

    return diagnose_payment(context)


# ---------------------------------------------------------
# Policy & Safety Engine
# ---------------------------------------------------------

@app.get("/policy/{payment_id}")
def check_policy(
    payment_id: int,
    db: Session = Depends(get_db)
):

    # Find payment
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:
        return {
            "error": "Payment not found"
        }

    # Build complete payment context
    context = build_payment_context(
        payment_id,
        db
    )

    if not context:
        return {
            "error": "Payment context could not be built"
        }

    # Generate AI diagnosis
    diagnosis = diagnose_payment(context)

    # Evaluate diagnosis using Policy Engine
    policy_result = evaluate_policy(
        payment=payment,
        diagnosis=diagnosis
    )

    return policy_result


# ---------------------------------------------------------
# Execute Recovery
# ---------------------------------------------------------

@app.get("/execute-recovery/{payment_id}")
def execute_payment_recovery(payment_id: int, db: Session = Depends(get_db)):

    # Find payment
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:
        return {"error": "Payment not found"}

    # Build payment context
    context = build_payment_context(payment_id, db)

    if not context:
        return {"error": "Payment context could not be built"}

    # Generate AI diagnosis
    diagnosis = diagnose_payment(context)

    # Evaluate diagnosis through Policy & Safety Engine
    policy_result = evaluate_policy(
        payment=payment,
        diagnosis=diagnosis
    )

    # Execute only the policy-approved action
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
# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):

    # Get all payments
    payments = db.query(models.Payment).all()

    # Get all payment attempts
    attempts = db.query(models.PaymentAttempt).all()

    # Calculate dashboard statistics
    total_payments = len(payments)

    failed_payments = len([
        payment for payment in payments
        if payment.status == "failed"
    ])

    executed_actions = len([
        attempt for attempt in attempts
        if attempt.status in [
            "retry_scheduled",
            "waiting_for_funds",
            "customer_action_required",
            "bank_contact_required"
        ]
    ])

    blocked_actions = len([
        attempt for attempt in attempts
        if attempt.status == "retry_blocked"
    ])

    human_review_cases = len([
        attempt for attempt in attempts
        if attempt.status == "human_review_required"
    ])

    return {
        "statistics": {
            "total_payments": total_payments,
            "failed_payments": failed_payments,
            "executed_actions": executed_actions,
            "blocked_actions": blocked_actions,
            "human_review_cases": human_review_cases
        },
        "payments": [
            {
                "payment_id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "failure_reason": payment.failure_reason
            }
            for payment in payments
        ],
        "payment_attempts": [
            {
                "attempt_id": attempt.id,
                "payment_id": attempt.payment_id,
                "status": attempt.status,
                "failure_reason": attempt.failure_reason
            }
            for attempt in attempts
        ]
    }    
# ---------------------------------------------------------
# Razorpay Test Order
# ---------------------------------------------------------

@app.post("/razorpay/test-order")
def create_razorpay_test_order(
    db: Session = Depends(get_db)
):
    try:
        order = create_test_order(100)

        return {
            "status": "success",
            "message": "Razorpay Test Mode order created.",
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"]
        }

    except Exception as e:
        return {
            "status": "failed",
            "message": "Unable to create Razorpay test order.",
            "error": str(e)
        }
# ---------------------------------------------------------
# Metrics & Evaluation
# ---------------------------------------------------------

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    return calculate_metrics(db)