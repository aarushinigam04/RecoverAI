from backend import models
from backend.database import SessionLocal


def reconcile_experiment():

    db = SessionLocal()

    try:
        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like("RECOVERAI-EXP-%")
            )
            .order_by(models.Payment.id)
            .all()
        )

        print()
        print("=" * 80)
        print("RecoverAI Experiment Reconciliation")
        print("=" * 80)

        print(f"\nExperiment payments: {len(payments)}")

        successful = 0
        retry_failed = 0
        pending = 0
        blocked = 0

        print()
        print(
            f"{'Payment':<10}"
            f"{'Status':<12}"
            f"{'Original Reason':<32}"
            f"{'Execution Attempt':<22}"
        )
        print("-" * 80)

        for payment in payments:

            attempts = (
                db.query(models.PaymentAttempt)
                .filter(
                    models.PaymentAttempt.payment_id
                    == payment.id
                )
                .order_by(models.PaymentAttempt.id)
                .all()
            )

            original_reason = (
                attempts[0].failure_reason
                if attempts
                else payment.failure_reason
            )

            execution_attempts = attempts[1:]

            execution_status = "none"

            if payment.status == "success":
                successful += 1
                execution_status = "SUCCESS"

            elif execution_attempts:

                latest = execution_attempts[-1]

                if latest.status == "failed":
                    retry_failed += 1
                    execution_status = "FAILED"

                elif latest.status in (
                    "customer_action_required",
                    "waiting_for_funds",
                    "bank_contact_required",
                    "human_review_required",
                ):
                    pending += 1
                    execution_status = latest.status.upper()

            else:
                blocked += 1
                execution_status = "BLOCKED"

            print(
                f"{payment.id:<10}"
                f"{payment.status:<12}"
                f"{str(original_reason):<32}"
                f"{execution_status:<22}"
            )

        print()
        print("=" * 80)
        print("DATABASE-RECONCILED TOTALS")
        print("=" * 80)

        print(f"Successful recoveries : {successful}")
        print(f"Failed executions     : {retry_failed}")
        print(f"Pending actions       : {pending}")
        print(f"Blocked payments      : {blocked}")

        print()
        print(
            f"Total accounted       : "
            f"{successful + retry_failed + pending + blocked}"
        )

        print()
        print("=" * 80)
        print("READ-ONLY RECONCILIATION")
        print("=" * 80)
        print("No payment records were modified.")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    reconcile_experiment()