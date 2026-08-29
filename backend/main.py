from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from types import SimpleNamespace

from backend.database import Base, engine, SessionLocal
from backend import models
from backend.recovery import get_recovery_recommendation
from backend.ai_agent import diagnose_payment
from backend.context_builder import build_payment_context
from backend.policy_engine import evaluate_policy
from backend.recovery_executor import execute_recovery


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(title="RecoverAI")


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