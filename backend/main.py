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

app = FastAPI(
    title="RecoverAI",
    description="AI-assisted payment recovery system",
    version="1.0.0"
)


# =========================================================
# DASHBOARD FRONTEND
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"

app.mount(
    "/dashboard-ui",
    StaticFiles(
        directory=str(DASHBOARD_DIR),
        html=True
    ),
    name="dashboard-ui"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
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
        .filter(
            models.Payment.status == "failed"
        )
        .order_by(models.Payment.id)
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
        .filter(
            models.Payment.id == payment_id
        )
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
        .filter(
            models.Payment.id == payment_id
        )
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
        .filter(
            models.Payment.id == payment_id
        )
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
    # AI DIAGNOSIS
    # -----------------------------------------------------

    diagnosis = diagnose_payment(
        context
    )

    # -----------------------------------------------------
    # POLICY EVALUATION
    # -----------------------------------------------------

    policy_result = evaluate_policy(
        payment=payment,
        diagnosis=diagnosis
    )

    # -----------------------------------------------------
    # EXECUTE ONLY APPROVED ACTION
    # -----------------------------------------------------

    execution_result = execute_recovery(
        payment=payment,
        policy_result=policy_result,
        db=db
    )

    return {

        "payment_id":
            payment_id,

        "diagnosis":
            diagnosis,

        "policy":
            policy_result,

        "execution":
            execution_result
    }


# =========================================================
# DASHBOARD API
# =========================================================

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    # =====================================================
    # GET PAYMENTS
    # =====================================================

    payments = (
        db.query(models.Payment)
        .order_by(models.Payment.id)
        .all()
    )

    # =====================================================
    # GET PAYMENT ATTEMPTS
    # =====================================================

    attempts = (
        db.query(models.PaymentAttempt)
        .order_by(models.PaymentAttempt.id)
        .all()
    )

    # =====================================================
    # PAYMENT STATISTICS
    # =====================================================

    total_payments = len(payments)

    failed_payments = [
        payment
        for payment in payments
        if payment.status == "failed"
    ]

    successful_payments = [
        payment
        for payment in payments
        if payment.status in [
            "success",
            "captured",
            "paid"
        ]
    ]

    failed_count = len(
        failed_payments
    )

    successful_count = len(
        successful_payments
    )

    # =====================================================
    # RECOVERY ATTEMPTS
    # =====================================================

    successful_attempts = [
        attempt
        for attempt in attempts
        if attempt.status == "success"
    ]

    executed_attempts = [
        attempt
        for attempt in attempts
        if attempt.status in [
            "retry_scheduled",
            "waiting_for_funds",
            "customer_action_required",
            "bank_contact_required",
            "success"
        ]
    ]

    blocked_attempts = [
        attempt
        for attempt in attempts
        if attempt.status in [
            "retry_blocked",
            "blocked"
        ]
    ]

    human_attempts = [
        attempt
        for attempt in attempts
        if attempt.status in [
            "human_review_required",
            "needs_human"
        ]
    ]

    # =====================================================
    # CONFIRMED RECOVERIES
    # =====================================================

    recovered_payment_ids = set()

    for attempt in successful_attempts:

        if attempt.payment_id is not None:

            recovered_payment_ids.add(
                attempt.payment_id
            )

    confirmed_successful_payments = len(
        recovered_payment_ids
    )

    # =====================================================
    # PAYMENT LOOKUP
    # =====================================================

    payment_lookup = {
        payment.id: payment
        for payment in payments
    }

    # =====================================================
    # RECOVERED REVENUE
    #
    # Each recovered payment is counted only once.
    # =====================================================

    recovered_amount = 0.0

    for payment_id in recovered_payment_ids:

        payment = payment_lookup.get(
            payment_id
        )

        if payment:

            recovered_amount += float(
                payment.amount
            )

    # =====================================================
    # REVENUE AT RISK
    #
    # Current failed-payment cohort.
    # =====================================================

    revenue_at_risk = sum(
        float(payment.amount)
        for payment in failed_payments
    )

    # =====================================================
    # RECOVERY RATE
    #
    # IMPORTANT:
    #
    # This is based on the current database cohort:
    #
    # recovered payments /
    # (currently failed + recovered payments)
    #
    # This prevents successful recovered payments from
    # disappearing from the denominator after execution.
    # =====================================================

    recovery_denominator = (
        failed_count
        + confirmed_successful_payments
    )

    recovery_rate = 0.0

    if recovery_denominator > 0:

        recovery_rate = round(
            (
                confirmed_successful_payments
                / recovery_denominator
            ) * 100,
            2
        )

    # =====================================================
    # EXECUTION SUCCESS RATE
    # =====================================================

    execution_success_rate = 0.0

    if len(executed_attempts) > 0:

        execution_success_rate = round(
            (
                len(successful_attempts)
                / len(executed_attempts)
            ) * 100,
            2
        )

    # =====================================================
    # FAILURE ANALYSIS
    # =====================================================

    failure_analysis_map = {}

    for payment in failed_payments:

        reason = (
            payment.failure_reason
            or "Unknown"
        )

        failure_analysis_map[reason] = (
            failure_analysis_map.get(
                reason,
                0
            ) + 1
        )

    failure_analysis = [

        {
            "reason": reason,
            "count": count
        }

        for reason, count
        in sorted(
            failure_analysis_map.items(),
            key=lambda item: item[1],
            reverse=True
        )
    ]

    # =====================================================
    # ATTEMPT STATUS ANALYSIS
    # =====================================================

    attempt_status_analysis = {}

    for attempt in attempts:

        status = (
            attempt.status
            or "unknown"
        )

        attempt_status_analysis[status] = (
            attempt_status_analysis.get(
                status,
                0
            ) + 1
        )

    # =====================================================
    # RECENT PAYMENTS
    # =====================================================

    recent_payments = (
        payments[-10:][::-1]
    )

    # =====================================================
    # AI DECISION PREVIEW
    #
    # IMPORTANT:
    # This is READ-ONLY.
    #
    # Loading the dashboard must NEVER execute a
    # recovery action.
    # =====================================================

    ai_decision = None

    preview_payment = next(
        (
            payment
            for payment in payments
            if payment.status == "failed"
        ),
        None
    )

    if preview_payment:

        try:

            context = build_payment_context(
                preview_payment.id,
                db
            )

            if context:

                diagnosis = diagnose_payment(
                    context
                )

                policy = evaluate_policy(
                    payment=preview_payment,
                    diagnosis=diagnosis
                )

                ai_decision = {

                    "payment_id":
                        preview_payment.id,

                    "amount":
                        float(
                            preview_payment.amount
                        ),

                    "failure_reason":
                        preview_payment.failure_reason,

                    "diagnosis":
                        diagnosis,

                    "policy":
                        policy
                }

        except Exception:

            ai_decision = {
                "error":
                    "AI preview unavailable"
            }

    # =====================================================
    # PAYMENT DATA
    # =====================================================

    payment_data = [

        {
            "payment_id":
                payment.id,

            "amount":
                float(payment.amount),

            "currency":
                payment.currency,

            "status":
                payment.status,

            "failure_reason":
                payment.failure_reason
        }

        for payment in payments
    ]

    # =====================================================
    # PAYMENT ATTEMPT DATA
    # =====================================================

    attempt_data = [

        {
            "attempt_id":
                attempt.id,

            "payment_id":
                attempt.payment_id,

            "status":
                attempt.status,

            "failure_reason":
                attempt.failure_reason
        }

        for attempt in attempts
    ]

    # =====================================================
    # FINAL DASHBOARD RESPONSE
    # =====================================================

    return {

        "statistics": {

            "total_payments":
                total_payments,

            "failed_payments":
                failed_count,

            "successful_payments":
                successful_count,

            "executed_actions":
                len(executed_attempts),

            "blocked_actions":
                len(blocked_attempts),

            "human_review_cases":
                len(human_attempts),

            "confirmed_successful_payments":
                confirmed_successful_payments,

            "confirmed_payment_recovery_rate_percent":
                recovery_rate,

            "execution_success_rate_percent":
                execution_success_rate,

            "recovered_amount":
                round(
                    recovered_amount,
                    2
                ),

            "revenue_at_risk":
                round(
                    revenue_at_risk,
                    2
                )
        },

        "failure_analysis":
            failure_analysis,

        "attempt_status_analysis":
            attempt_status_analysis,

        "ai_decision":
            ai_decision,

        "recent_payments": [

            {
                "payment_id":
                    payment.id,

                "amount":
                    float(payment.amount),

                "currency":
                    payment.currency,

                "status":
                    payment.status,

                "failure_reason":
                    payment.failure_reason
            }

            for payment
            in recent_payments
        ],

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

        # -------------------------------------------------
        # TEST MODE ONLY
        # -------------------------------------------------

        order = create_test_order(
            100
        )

        return {

            "status":
                "success",

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

            "status":
                "failed",

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