from backend.database import SessionLocal
from backend.models import Payment
from backend.action_executor import (
    simulate_test_outcome,
    get_test_success_probability
)

db = SessionLocal()

try:
    payments = (
        db.query(Payment)
        .filter(
            Payment.order_id.like("RECOVERAI-EXP-%"),
            Payment.status == "failed"
        )
        .order_by(Payment.id)
        .all()
    )

    print("Successful retry candidates:")
    print("-" * 70)

    for payment in payments:
        action = "retry_payment"

        try:
            probability = get_test_success_probability(
                payment,
                action
            )
        except KeyError:
            # Category is not part of the frozen synthetic
            # retry outcome model.
            continue

        if probability > 0:
            success = simulate_test_outcome(
                payment,
                action,
                probability
            )

            if success:
                print(
                    f"ID {payment.id} | "
                    f"₹{payment.amount} | "
                    f"{payment.failure_reason} | "
                    f"probability={probability} | "
                    f"simulated_success=True"
                )

finally:
    db.close()