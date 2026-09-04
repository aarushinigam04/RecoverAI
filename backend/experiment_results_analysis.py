from collections import defaultdict

from backend import models
from backend.database import SessionLocal


def run_experiment_results_analysis():

    db = SessionLocal()

    try:

        # ====================================================
        # LOAD EXPERIMENT COHORT
        # ====================================================

        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like(
                    "RECOVERAI-EXP-%"
                )
            )
            .order_by(models.Payment.id)
            .all()
        )

        if not payments:
            print("No experiment payments found.")
            return

        # ====================================================
        # RESULT STORAGE
        # ====================================================

        results = defaultdict(
            lambda: {
                "payments": 0,
                "retry": 0,
                "payment_link": 0,
                "successful": 0,
                "failed": 0,
                "pending": 0,
                "blocked": 0,
                "recovered_amount": 0.0,
            }
        )

        total_successful = 0
        total_failed = 0
        total_pending = 0
        total_blocked = 0
        total_recovered_amount = 0.0

        # ====================================================
        # ANALYZE EACH PAYMENT
        # ====================================================

        for payment in payments:

            # ------------------------------------------------
            # GET ALL ATTEMPTS FOR THIS PAYMENT
            # ------------------------------------------------

            attempts = (
                db.query(models.PaymentAttempt)
                .filter(
                    models.PaymentAttempt.payment_id
                    == payment.id
                )
                .order_by(
                    models.PaymentAttempt.id
                )
                .all()
            )

            if not attempts:

                category = "unknown"

                results[category]["payments"] += 1
                results[category]["blocked"] += 1

                total_blocked += 1

                continue

            # ------------------------------------------------
            # ORIGINAL FAILURE REASON
            #
            # The first attempt was created by experiment_seed
            # and preserves the original failure reason.
            # ------------------------------------------------

            original_reason = attempts[0].failure_reason

            if original_reason:

                category = (
                    original_reason
                    .strip()
                    .lower()
                )

            else:

                category = "unknown"

            results[category]["payments"] += 1

            # ------------------------------------------------
            # FIND EXPERIMENT EXECUTION ATTEMPTS
            #
            # The first attempt belongs to the original
            # failed payment. Later attempts belong to the
            # experiment execution.
            # ------------------------------------------------

            execution_attempts = attempts[1:]

            if not execution_attempts:

                # No execution attempt means the payment
                # was blocked or otherwise not executed.

                results[category]["blocked"] += 1
                total_blocked += 1

                continue

            # ------------------------------------------------
            # USE THE LATEST EXECUTION ATTEMPT
            # ------------------------------------------------

            latest_attempt = execution_attempts[-1]

            attempt_status = (
                latest_attempt.status
                or ""
            ).strip().lower()

            # ------------------------------------------------
            # CONFIRMED SUCCESS
            # ------------------------------------------------

            if attempt_status == "success":

                results[category]["retry"] += 1
                results[category]["successful"] += 1

                amount = float(
                    payment.amount
                )

                results[category][
                    "recovered_amount"
                ] += amount

                total_successful += 1
                total_recovered_amount += amount

            # ------------------------------------------------
            # FAILED RETRY
            # ------------------------------------------------

            elif attempt_status == "failed":

                results[category]["retry"] += 1
                results[category]["failed"] += 1

                total_failed += 1

            # ------------------------------------------------
            # CUSTOMER PAYMENT-LINK ACTION
            # ------------------------------------------------

            elif (
                attempt_status
                == "customer_action_required"
            ):

                results[category]["payment_link"] += 1
                results[category]["pending"] += 1

                total_pending += 1

            # ------------------------------------------------
            # OTHER PENDING STATES
            # ------------------------------------------------

            elif attempt_status in {
                "waiting_for_funds",
                "bank_contact_required",
                "human_review_required",
            }:

                results[category]["pending"] += 1
                total_pending += 1

            # ------------------------------------------------
            # UNKNOWN
            # ------------------------------------------------

            else:

                results[category]["blocked"] += 1
                total_blocked += 1

        # ====================================================
        # OUTPUT
        # ====================================================

        print()
        print("=" * 105)
        print("RecoverAI Experiment Results Analysis")
        print("=" * 105)

        print()

        header = (
            f"{'Category':<32}"
            f"{'Payments':>10}"
            f"{'Retry':>8}"
            f"{'Link':>8}"
            f"{'Success':>10}"
            f"{'Failed':>9}"
            f"{'Pending':>10}"
            f"{'Recovered ₹':>17}"
        )

        print(header)
        print("-" * 105)

        for category, data in results.items():

            print(
                f"{category:<32}"
                f"{data['payments']:>10}"
                f"{data['retry']:>8}"
                f"{data['payment_link']:>8}"
                f"{data['successful']:>10}"
                f"{data['failed']:>9}"
                f"{data['pending']:>10}"
                f"{data['recovered_amount']:>17,.2f}"
            )

        print("-" * 105)

        # ====================================================
        # OVERALL RESULTS
        # ====================================================

        total = len(payments)

        recovery_rate = (
            total_successful / total * 100
            if total > 0
            else 0
        )

        execution_rate = (
            (
                total_successful
                + total_failed
                + total_pending
            )
            / total
            * 100
            if total > 0
            else 0
        )

        print()
        print(
            f"Total experiment payments : "
            f"{total}"
        )

        print(
            f"Successful recoveries     : "
            f"{total_successful}"
        )

        print(
            f"Failed executions         : "
            f"{total_failed}"
        )

        print(
            f"Pending actions           : "
            f"{total_pending}"
        )

        print(
            f"Blocked payments          : "
            f"{total_blocked}"
        )

        print(
            f"Confirmed recovery rate   : "
            f"{recovery_rate:.2f}%"
        )

        print(
            f"Execution coverage        : "
            f"{execution_rate:.2f}%"
        )

        print(
            f"Recovered revenue         : "
            f"₹{total_recovered_amount:,.2f}"
        )

        # ====================================================
        # IMPORTANT NOTE
        # ====================================================

        print()
        print("=" * 105)
        print("READ-ONLY RESULT ANALYSIS")
        print("=" * 105)

        print(
            "This script only reads experiment records."
        )

        print(
            "No payment records were modified."
        )

        print(
            "Original failure categories are taken from "
            "the first PaymentAttempt."
        )

        print(
            "Recovered revenue represents confirmed "
            "successful outcomes from the controlled "
            "Test Mode experiment."
        )

        print("=" * 105)

    finally:

        db.close()


if __name__ == "__main__":
    run_experiment_results_analysis()