from backend.database import SessionLocal
from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment


def main():
    db = SessionLocal()

    try:
        payments = (
            db.query(
                __import__("backend.models", fromlist=["Payment"]).Payment
            )
            .filter(
                __import__("backend.models", fromlist=["Payment"]).Payment.order_id.like(
                    "RECOVERAI-ORD-%"
                )
            )
            .order_by(
                __import__("backend.models", fromlist=["Payment"]).Payment.id
            )
            .all()
        )

        print("=" * 70)
        print("RecoverAI 500-Payment Diagnosis Audit")
        print("=" * 70)

        print(f"Payments found: {len(payments)}")
        print()

        mismatches = 0

        for payment in payments:
            context = build_payment_context(payment.id, db)
            diagnosis = diagnose_payment(context)

            actual = payment.failure_reason or ""
            predicted = diagnosis["diagnosis"]["category"]

            # Normalize only for comparison.
            actual_norm = actual.lower().strip()
            predicted_norm = predicted.lower().strip()

            if actual_norm not in predicted_norm and predicted_norm not in actual_norm:
                mismatches += 1

                print(
                    f"ID {payment.id} | "
                    f"Reason: {actual} | "
                    f"Predicted: {predicted} | "
                    f"Action: {diagnosis['recovery']['recommended_action']} | "
                    f"Confidence: {diagnosis['diagnosis']['confidence']}"
                )

        print()
        print("=" * 70)
        print(f"Diagnosis mismatches found: {mismatches}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()