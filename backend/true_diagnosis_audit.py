from backend.database import SessionLocal
from backend import models
from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment
from backend.evaluation import get_category, normalize_reason


def main():
    db = SessionLocal()

    try:
        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like("RECOVERAI-ORD-%")
            )
            .order_by(models.Payment.id)
            .all()
        )

        total = len(payments)
        correct = 0
        incorrect = 0

        error_breakdown = {}

        print("=" * 70)
        print("TRUE 500-PAYMENT DIAGNOSIS AUDIT")
        print("=" * 70)
        print(f"Payments: {total}")
        print()

        for payment in payments:

            reason = normalize_reason(
                payment.failure_reason
            )

            expected_category = get_category(reason)

            if expected_category is None:
                expected_category = "unknown"

            context = build_payment_context(
                payment.id,
                db
            )

            diagnosis = diagnose_payment(context)

            diagnosed_category = normalize_reason(
                diagnosis
                .get("diagnosis", {})
                .get("category", "")
            )

            diagnosis_category_map = {
                "insufficient funds":
                    "insufficient funds",

                "card expired":
                    "card expired",

                "bank timeout":
                    "bank timeout",

                "gateway timeout":
                    "gateway timeout",

                "payment api unavailable":
                    "payment api unavailable",

                "network timeout":
                    "network timeout",

                "network connectivity issue":
                    "network connectivity issue",

                "fraud detected":
                    "fraud detected",

                "customer opted out":
                    "customer opted out",
            }

            normalized_diagnosed_category = (
                diagnosis_category_map.get(
                    diagnosed_category,
                    diagnosed_category
                )
            )

            if normalized_diagnosed_category == expected_category:
                correct += 1
            else:
                incorrect += 1

                key = (
                    expected_category,
                    normalized_diagnosed_category
                )

                error_breakdown[key] = (
                    error_breakdown.get(key, 0) + 1
                )

        accuracy = (
            correct / total * 100
            if total
            else 0
        )

        print("=" * 70)
        print("RESULT")
        print("=" * 70)

        print(f"Correct diagnoses:   {correct}")
        print(f"Incorrect diagnoses: {incorrect}")
        print(f"Diagnosis accuracy:  {accuracy:.2f}%")
        print()

        print("=" * 70)
        print("ACTUAL DIAGNOSIS ERROR BREAKDOWN")
        print("=" * 70)

        if not error_breakdown:
            print("No diagnosis errors found.")
        else:
            for (expected, predicted), count in sorted(
                error_breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(
                    f"{count:3} | "
                    f"Expected: {expected:<30} | "
                    f"Predicted: {predicted}"
                )

        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()