from collections import Counter

from backend.database import SessionLocal
from backend import models


def main():
    db = SessionLocal()

    try:
        payments = (
            db.query(models.Payment)
            .filter(models.Payment.order_id.like("RECOVERAI-ORD-%"))
            .order_by(models.Payment.id)
            .all()
        )

        print("=" * 70)
        print("500-COHORT VERIFICATION")
        print("=" * 70)

        print("Total benchmark payments:", len(payments))

        status_counts = Counter(
            payment.status for payment in payments
        )

        print("\nStatus distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

        failure_counts = Counter(
            (payment.failure_reason or "").strip().lower()
            for payment in payments
        )

        print("\nFailure-reason distribution:")
        for reason, count in failure_counts.most_common():
            print(f"  {reason}: {count}")

        high_value = sum(
            1 for payment in payments
            if (payment.amount or 0) >= 50000
        )

        print("\nHigh-value payments:", high_value)

        print("\nPayment ID range:")
        if payments:
            print("  First:", payments[0].id)
            print("  Last :", payments[-1].id)

        print("\nOrder ID range:")
        if payments:
            print("  First:", payments[0].order_id)
            print("  Last :", payments[-1].order_id)

        print("=" * 70)
        print("Read-only verification completed.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()