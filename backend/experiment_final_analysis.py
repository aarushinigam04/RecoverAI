from collections import defaultdict

from backend import models
from backend.database import SessionLocal


def run_final_analysis():

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

        if not payments:
            print("No experiment payments found.")
            return

        category_stats = defaultdict(
            lambda: {
                "payments": 0,
                "success": 0,
                "failed": 0,
                "pending": 0,
                "blocked": 0,
                "recovered": 0.0,
            }
        )

        total_success = 0
        total_failed = 0
        total_pending = 0
        total_blocked = 0
        total_recovered = 0.0

        # ---------------------------------------------------------
        # Analyze every experiment payment
        # ---------------------------------------------------------

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

            if not attempts:
                category = (
                    payment.failure_reason
                    or "unknown"
                )
            else:
                category = (
                    attempts[0].failure_reason
                    or "unknown"
                )

            category = str(category).lower()

            stats = category_stats[category]
            stats["payments"] += 1

            # -----------------------------------------------------
            # Determine final outcome
            # -----------------------------------------------------

            if payment.status == "success":

                stats["success"] += 1
                total_success += 1

                stats["recovered"] += float(
                    payment.amount
                )

                total_recovered += float(
                    payment.amount
                )

                continue

            # Look at all attempts after the original attempt.
            execution_attempts = attempts[1:]

            if not execution_attempts:

                stats["blocked"] += 1
                total_blocked += 1

                continue

            latest_attempt = execution_attempts[-1]

            if latest_attempt.status == "failed":

                stats["failed"] += 1
                total_failed += 1

            elif latest_attempt.status in (
                "customer_action_required",
                "waiting_for_funds",
                "bank_contact_required",
                "human_review_required",
            ):

                stats["pending"] += 1
                total_pending += 1

            else:

                stats["pending"] += 1
                total_pending += 1

        # ---------------------------------------------------------
        # Print category analysis
        # ---------------------------------------------------------

        print()
        print("=" * 105)
        print("RecoverAI Final Experiment Analysis")
        print("=" * 105)

        print()

        print(
            f"{'Category':<32}"
            f"{'Payments':>10}"
            f"{'Success':>10}"
            f"{'Failed':>10}"
            f"{'Pending':>10}"
            f"{'Blocked':>10}"
            f"{'Recovery %':>12}"
            f"{'Recovered ₹':>16}"
        )

        print("-" * 105)

        for category, stats in sorted(
            category_stats.items(),
            key=lambda item: item[0]
        ):

            recovery_rate = (
                stats["success"]
                / stats["payments"]
                * 100
                if stats["payments"] > 0
                else 0
            )

            print(
                f"{category:<32}"
                f"{stats['payments']:>10}"
                f"{stats['success']:>10}"
                f"{stats['failed']:>10}"
                f"{stats['pending']:>10}"
                f"{stats['blocked']:>10}"
                f"{recovery_rate:>11.2f}%"
                f"{stats['recovered']:>16,.2f}"
            )

        # ---------------------------------------------------------
        # Overall metrics
        # ---------------------------------------------------------

        total = len(payments)

        recovery_rate = (
            total_success / total * 100
            if total > 0
            else 0
        )

        execution_coverage = (
            (
                total_success
                + total_failed
                + total_pending
            )
            / total
            * 100
            if total > 0
            else 0
        )

        print()
        print("=" * 105)
        print("FINAL EXPERIMENT METRICS")
        print("=" * 105)

        print()

        print(
            f"Experiment payments      : {total}"
        )

        print(
            f"Successful recoveries    : {total_success}"
        )

        print(
            f"Failed executions        : {total_failed}"
        )

        print(
            f"Pending actions          : {total_pending}"
        )

        print(
            f"Blocked payments         : {total_blocked}"
        )

        print(
            f"Confirmed recovery rate  : "
            f"{recovery_rate:.2f}%"
        )

        print(
            f"Execution coverage      : "
            f"{execution_coverage:.2f}%"
        )

        print(
            f"Recovered revenue        : "
            f"₹{total_recovered:,.2f}"
        )

        print()
        print("=" * 105)
        print("READ-ONLY FINAL ANALYSIS")
        print("=" * 105)

        print(
            "This script only reads experiment records."
        )

        print(
            "No payment records were modified."
        )

        print(
            "Recovered revenue represents confirmed "
            "successful outcomes from the controlled "
            "Test Mode experiment."
        )

        print(
            "These results do not represent real-world "
            "customer payment behavior."
        )

        print("=" * 105)

    finally:
        db.close()


if __name__ == "__main__":
    run_final_analysis()