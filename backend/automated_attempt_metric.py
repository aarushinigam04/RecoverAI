from backend.database import SessionLocal
from backend.models import Payment
from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy


db = SessionLocal()

try:

    payments = (
        db.query(Payment)
        .filter(
            Payment.order_id.like("RECOVERAI-ORD-%")
        )
        .order_by(Payment.id)
        .all()
    )

    print("=" * 70)
    print("RecoverAI — Automated Attempt Metric")
    print("=" * 70)

    print(f"Evaluation cohort: {len(payments)} payments")

    automated = 0
    human_review = 0
    blocked = 0

    automated_attempt_value = 0.0
    expected_recovered = 0.0

    for payment in payments:

        # Build the same context used by the AI pipeline.
        context = build_payment_context(
            payment.id,
            db
        )

        if not context:
            continue

        # AI diagnosis expects the context dictionary.
        diagnosis = diagnose_payment(context)

        # Apply the existing frozen V2 policy.
        policy = evaluate_policy(
            payment,
            diagnosis
        )

        decision = policy.get(
            "policy_decision"
        )

        approved_action = policy.get(
            "approved_action"
        )

        # Only an approved retry_payment represents
        # an actual automated payment attempt.
        if (
            decision == "APPROVED"
            and approved_action == "retry_payment"
        ):

            automated += 1

            probability = (
                diagnosis
                .get("recovery", {})
                .get("success_probability", 0)
            )

            automated_attempt_value += float(
                payment.amount or 0
            )

            expected_recovered += (
                float(payment.amount or 0)
                * probability
            )

        elif decision == "NEEDS_HUMAN":

            human_review += 1

        elif decision == "BLOCKED":

            blocked += 1

    print()
    print("=" * 70)
    print("AUTOMATED ATTEMPT FUNNEL")
    print("=" * 70)

    print(
        f"Automated retry attempts: {automated}"
    )

    print(
        f"Human review:             {human_review}"
    )

    print(
        f"Blocked:                  {blocked}"
    )

    print()
    print(
        f"Automated attempt value: "
        f"₹{automated_attempt_value:.2f}"
    )

    print(
        f"Expected recovered value: "
        f"₹{expected_recovered:.2f}"
    )

    if automated_attempt_value > 0:

        automated_rate = (
            expected_recovered
            / automated_attempt_value
        ) * 100

    else:

        automated_rate = 0

    print()
    print(
        f"Automated-attempt recovery rate: "
        f"{automated_rate:.2f}%"
    )

    print("=" * 70)
    print("Read-only calculation completed.")
    print("=" * 70)

finally:

    db.close()