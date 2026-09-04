from collections import Counter

from backend.database import SessionLocal
from backend import models
from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy


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
        print("500-COHORT POLICY ACTION AUDIT")
        print("=" * 70)

        print("Payments:", len(payments))

        actions = Counter()
        decisions = Counter()
        categories = Counter()

        safety_violations = []

        for payment in payments:

            context = build_payment_context(
                payment.id,
                db
            )

            diagnosis = diagnose_payment(context)

            policy = evaluate_policy(
                payment=payment,
                diagnosis=diagnosis
            )

            decision = policy.get(
                "policy_decision"
            )

            action = policy.get(
                "approved_action"
            )

            diagnosed_category = (
                diagnosis
                .get("diagnosis", {})
                .get("category", "Unknown")
            )

            decisions[decision] += 1
            actions[action] += 1
            categories[diagnosed_category] += 1

            reason = (
                payment.failure_reason or ""
            ).lower()

            is_high_value = (
                (payment.amount or 0) >= 50000
            )

            is_restricted = any(
                phrase in reason
                for phrase in [
                    "fraud",
                    "customer opted out",
                    "payment already captured",
                    "duplicate webhook",
                    "retry limit exceeded"
                ]
            )

            # Safety audit
            if is_high_value:
                if action != "require_human_review":
                    safety_violations.append(
                        (
                            payment.id,
                            reason,
                            "high_value",
                            decision,
                            action
                        )
                    )

            if is_restricted:
                if action not in [
                    "do_not_retry",
                    "require_human_review"
                ]:
                    safety_violations.append(
                        (
                            payment.id,
                            reason,
                            "restricted",
                            decision,
                            action
                        )
                    )

        print()
        print("-" * 70)
        print("POLICY DECISIONS")
        print("-" * 70)

        for key, value in decisions.items():
            print(f"{key}: {value}")

        print()
        print("-" * 70)
        print("APPROVED ACTIONS")
        print("-" * 70)

        for key, value in actions.most_common():
            print(f"{key}: {value}")

        print()
        print("-" * 70)
        print("DIAGNOSED CATEGORIES")
        print("-" * 70)

        for key, value in categories.most_common():
            print(f"{key}: {value}")

        retry = actions.get(
            "retry_payment",
            0
        )

        payment_link = actions.get(
            "ask_customer_to_update_payment_method",
            0
        )

        contact_bank = actions.get(
            "ask_customer_to_contact_bank",
            0
        )

        customer_actions = (
            payment_link +
            contact_bank
        )

        automated_actions = (
            retry +
            customer_actions
        )

        print()
        print("-" * 70)
        print("AUTOMATION BREAKDOWN")
        print("-" * 70)

        print("Retry payment:", retry)
        print("Payment-link:", payment_link)
        print("Contact bank:", contact_bank)
        print("Customer-directed actions:", customer_actions)
        print("Total automated actions:", automated_actions)

        if payments:
            print(
                "Automated action rate:",
                round(
                    automated_actions /
                    len(payments) * 100,
                    2
                ),
                "%"
            )

        print()
        print("-" * 70)
        print("SAFETY AUDIT")
        print("-" * 70)

        print(
            "Safety violations:",
            len(safety_violations)
        )

        if safety_violations:

            print()
            print("VIOLATING PAYMENTS:")

            for item in safety_violations:
                print(item)

        print()
        print("=" * 70)
        print("Read-only policy audit completed.")
        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":
    main()