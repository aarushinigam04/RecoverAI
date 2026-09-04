from collections import defaultdict

from backend import models
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy
from backend.action_executor import get_failure_category
from backend.evaluation import get_action_probability
from backend.database import SessionLocal


def run_experiment_analysis():

    db = SessionLocal()

    try:

        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like("RECOVERAI-EXP-%"),
                models.Payment.status == "failed"
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
                "approved": 0,
                "retry": 0,
                "payment_link": 0,
                "expected_recovery": 0.0
            }
        )

        total_expected_recovery = 0.0
        total_automated = 0

        print()
        print("=" * 75)
        print("RecoverAI Experiment Action Analysis")
        print("=" * 75)

        for payment in payments:

            payment_context = {
                "id": payment.id,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "failure_reason": payment.failure_reason,
            }

            diagnosis = diagnose_payment({
                "payment": payment_context
            })

            if not diagnosis:
                continue

            policy_result = evaluate_policy(
                payment,
                diagnosis
            )

            if not policy_result:
                continue

            decision = policy_result.get(
                "policy_decision"
            )

            action = policy_result.get(
                "approved_action"
            )

            category = get_failure_category(payment)

            stats = category_stats[category]

            stats["payments"] += 1

            if decision == "APPROVED":
                stats["approved"] += 1

            if (
                decision == "APPROVED"
                and action in {
                    "retry_payment",
                    "ask_customer_to_update_payment_method"
                }
            ):

                probability = get_action_probability(
                    category,
                    action
                )

                if probability is not None:

                    expected = (
                        float(payment.amount)
                        * probability
                    )

                    stats["expected_recovery"] += expected

                    total_expected_recovery += expected
                    total_automated += 1

            if action == "retry_payment":
                stats["retry"] += 1

            elif (
                action
                == "ask_customer_to_update_payment_method"
            ):
                stats["payment_link"] += 1

        print()
        print(
            f"{'Category':<32}"
            f"{'Payments':>10}"
            f"{'Approved':>10}"
            f"{'Retry':>10}"
            f"{'Link':>10}"
            f"{'Expected ₹':>15}"
        )

        print("-" * 87)

        for category, stats in sorted(
            category_stats.items(),
            key=lambda item: item[1]["expected_recovery"],
            reverse=True
        ):

            print(
                f"{str(category or 'unknown'):<32}"
                f"{stats['payments']:>10}"
                f"{stats['approved']:>10}"
                f"{stats['retry']:>10}"
                f"{stats['payment_link']:>10}"
                f"{stats['expected_recovery']:>15.2f}"
            )

        print("-" * 87)

        print()
        print(
            f"Automated opportunities : "
            f"{total_automated}"
        )

        print(
            f"Expected recovered ₹    : "
            f"{total_expected_recovery:.2f}"
        )

        print()
        print("=" * 75)
        print("READ-ONLY ANALYSIS")
        print("=" * 75)
        print("No recovery actions were executed.")
        print("No payment records were modified.")
        print("=" * 75)

    finally:
        db.close()


if __name__ == "__main__":
    run_experiment_analysis()