from backend.database import SessionLocal
from backend import models

from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy

from backend.evaluation import (
    get_recoverai_action,
)


def main():

    db = SessionLocal()

    try:

        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like(
                    "RECOVERAI-ORD-%"
                )
            )
            .order_by(models.Payment.id)
            .all()
        )

        print("=" * 70)
        print("500-COHORT DECISION RECONCILIATION")
        print("=" * 70)

        differences = []

        for payment in payments:

            context = build_payment_context(
                payment.id,
                db
            )

            diagnosis = diagnose_payment(
                context
            )

            policy = evaluate_policy(
                payment=payment,
                diagnosis=diagnosis
            )

            policy_decision = policy.get(
                "policy_decision"
            )

            approved_action = policy.get(
                "approved_action"
            )

            evaluation_action = get_recoverai_action(
                policy
            )

            # Convert evaluator action into the
            # corresponding policy classification.
            if evaluation_action == "human_review":
                evaluation_decision = "NEEDS_HUMAN"

            elif evaluation_action == "stop":
                evaluation_decision = "BLOCKED"

            elif evaluation_action in {
                "retry_payment",
                "payment_link"
            }:
                evaluation_decision = "APPROVED"

            else:
                evaluation_decision = "UNKNOWN"

            if policy_decision != evaluation_decision:

                differences.append({
                    "id": payment.id,
                    "order_id": payment.order_id,
                    "failure_reason": payment.failure_reason,
                    "amount": payment.amount,
                    "diagnosed_category": (
                        diagnosis
                        .get("diagnosis", {})
                        .get("category")
                    ),
                    "policy_decision": policy_decision,
                    "approved_action": approved_action,
                    "evaluation_action": evaluation_action,
                    "evaluation_decision": evaluation_decision,
                })

        print()
        print("Total payments:", len(payments))
        print("Decision differences:", len(differences))

        print()

        if differences:

            print("-" * 70)
            print("DIFFERING PAYMENTS")
            print("-" * 70)

            for item in differences:

                print()
                print("Payment ID:",
                      item["id"])

                print("Order ID:",
                      item["order_id"])

                print("Failure reason:",
                      item["failure_reason"])

                print("Amount:",
                      item["amount"])

                print("Diagnosed category:",
                      item["diagnosed_category"])

                print("Policy decision:",
                      item["policy_decision"])

                print("Approved action:",
                      item["approved_action"])

                print("Evaluation action:",
                      item["evaluation_action"])

                print("Evaluation decision:",
                      item["evaluation_decision"])

        else:

            print(
                "No policy/evaluation decision differences found."
            )

        print()
        print("=" * 70)
        print("Read-only reconciliation completed.")
        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":
    main()