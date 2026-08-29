from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from types import SimpleNamespace
from backend.database import Base, engine, SessionLocal
from backend import models
from backend.recovery import get_recovery_recommendation
from backend.ai_agent import diagnose_payment
from backend.context_builder import build_payment_context
from backend.policy_engine import evaluate_policy
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RecoverAI")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {
        "message": "RecoverAI is running!"
    }


@app.get("/payments/failed")
def get_failed_payments(db: Session = Depends(get_db)):
    payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "failed")
        .all()
    )

    return payments

@app.get("/recovery/test")
def test_recovery(failure_reason: str = ""):
    test_payment = SimpleNamespace(failure_reason=failure_reason)

    return get_recovery_recommendation(test_payment)
        

@app.get("/recovery/{payment_id}")
def get_recovery(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()

    if not payment:
        return {"error": "Payment not found"}

    return get_recovery_recommendation(payment)
@app.get("/ai-diagnosis/{payment_id}")
def ai_diagnosis(payment_id: int, db: Session = Depends(get_db)):
    context = build_payment_context(payment_id, db)

    if not context:
        return {"error": "Payment not found"}

    return diagnose_payment(context)

@app.get("/policy/{payment_id}")
def check_policy(payment_id: int, db: Session = Depends(get_db)):
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:
        return {"error": "Payment not found"}

    context = build_payment_context(payment_id, db)

    if not context:
        return {"error": "Payment context could not be built"}

    diagnosis = diagnose_payment(context)

    policy_result = evaluate_policy(
        payment=payment,
        diagnosis=diagnosis
    )

    return policy_result