from backend import models
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy
from backend.database import SessionLocal


def run_experiment_evaluation():

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

        retry_actions = 0
        payment_link_actions = 0
        stopped_actions = 0
        human_review_actions = 0
        unknown_actions = 0

        policy_approved = 0
        policy_blocked = 0
        policy_human_review = 0

        automated_opportunities = 0
        confidence_values = []

        print()
        print("=" * 70)
        print("RecoverAI Experiment Pre-Execution Evaluation")
        print("=" * 70)

        print(f"\nExperiment payments: {len(payments)}")

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
                unknown_actions += 1
                continue

            diagnosis_data = diagnosis.get(
                "diagnosis",
                {}
            )

            confidence = float(
                diagnosis_data.get(
                    "confidence",
                    0
                )
            )

            confidence_values.append(
                confidence
            )

            policy_result = evaluate_policy(
                payment,
                diagnosis
            )

            if not policy_result:
                unknown_actions += 1
                continue

            policy_decision = policy_result.get(
                "policy_decision",
                "UNKNOWN"
            )

            approved_action = policy_result.get(
                "approved_action",
                "unknown"
            )

            if policy_decision == "APPROVED":
                policy_approved += 1

            elif policy_decision == "BLOCKED":
                policy_blocked += 1

            elif policy_decision == "NEEDS_HUMAN":
                policy_human_review += 1

            if approved_action == "retry_payment":
                retry_actions += 1

            elif (
                approved_action
                == "ask_customer_to_update_payment_method"
            ):
                payment_link_actions += 1

            elif approved_action == "do_not_retry":
                stopped_actions += 1

            elif approved_action == "require_human_review":
                human_review_actions += 1

            else:
                unknown_actions += 1

            if (
                policy_decision == "APPROVED"
                and approved_action in {
                    "retry_payment",
                    "ask_customer_to_update_payment_method"
                }
            ):
                automated_opportunities += 1

        total = len(payments)

        automated_rate = (
            automated_opportunities / total * 100
            if total > 0 else 0
        )

        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
            * 100
            if confidence_values
            else 0
        )

        print()
        print("Decision Results")
        print("-" * 70)

        print(
            f"Retry payment actions       : "
            f"{retry_actions}"
        )

        print(
            f"Payment-link actions        : "
            f"{payment_link_actions}"
        )

        print(
            f"Stopped actions             : "
            f"{stopped_actions}"
        )

        print(
            f"Human review                : "
            f"{human_review_actions}"
        )

        print(
            f"Unknown actions             : "
            f"{unknown_actions}"
        )

        print()
        print("Policy Safety")
        print("-" * 70)

        print(
            f"Policy approved             : "
            f"{policy_approved}"
        )

        print(
            f"Policy blocked              : "
            f"{policy_blocked}"
        )

        print(
            f"Policy human review         : "
            f"{policy_human_review}"
        )

        print()
        print("Experiment Metrics")
        print("-" * 70)

        print(
            f"Automated recovery opportunities : "
            f"{automated_opportunities}"
        )

        print(
            f"Automated action rate            : "
            f"{automated_rate:.2f}%"
        )

        print(
            f"Average AI confidence            : "
            f"{average_confidence:.2f}%"
        )

        print()
        print("=" * 70)
        print("READ-ONLY PRE-EXECUTION BASELINE")
        print("=" * 70)
        print(
            "No recovery actions were executed."
        )
        print(
            "No payment records were modified."
        )
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_experiment_evaluation()