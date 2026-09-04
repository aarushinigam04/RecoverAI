from backend.database import SessionLocal
from backend import models
from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy


def run_operational_metrics(db, held_out_size=500):

    payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "failed")
        .order_by(models.Payment.id)
        .limit(held_out_size)
        .all()
    )

    total = len(payments)

    retry_attempts = 0
    payment_link_actions = 0
    human_review = 0
    blocked = 0
    unknown_actions = 0

    retry_value = 0.0
    payment_link_value = 0.0

    expected_retry_recovery = 0.0
    expected_payment_link_recovery = 0.0

    action_counts = {}

    for payment in payments:

        context = build_payment_context(
            payment.id,
            db
        )

        if not context:
            continue

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

        # --------------------------------------------------
        # HUMAN REVIEW
        # --------------------------------------------------

        if decision == "NEEDS_HUMAN":

            human_review += 1
            action_counts["human_review"] = (
                action_counts.get("human_review", 0) + 1
            )

            continue

        # --------------------------------------------------
        # BLOCKED
        # --------------------------------------------------

        if decision == "BLOCKED":

            blocked += 1
            action_counts["blocked"] = (
                action_counts.get("blocked", 0) + 1
            )

            continue

        # --------------------------------------------------
        # APPROVED ACTIONS
        # --------------------------------------------------

        if decision == "APPROVED":

            if action == "retry_payment":

                retry_attempts += 1

                amount = float(
                    payment.amount or 0
                )

                retry_value += amount

                probability = diagnosis.get(
                    "recovery", {}
                ).get(
                    "success_probability",
                    0
                )

                expected_retry_recovery += (
                    amount * probability
                )

                action_counts["retry_payment"] = (
                    action_counts.get(
                        "retry_payment",
                        0
                    ) + 1
                )

            elif action == (
                "ask_customer_to_update_payment_method"
            ):

                payment_link_actions += 1

                amount = float(
                    payment.amount or 0
                )

                payment_link_value += amount

                probability = diagnosis.get(
                    "recovery", {}
                ).get(
                    "success_probability",
                    0
                )

                expected_payment_link_recovery += (
                    amount * probability
                )

                action_counts["payment_link"] = (
                    action_counts.get(
                        "payment_link",
                        0
                    ) + 1
                )

            elif action == (
                "ask_customer_to_contact_bank"
            ):

                action_counts["contact_bank"] = (
                    action_counts.get(
                        "contact_bank",
                        0
                    ) + 1
                )

            elif action == "do_not_retry":

                blocked += 1

                action_counts["blocked"] = (
                    action_counts.get(
                        "blocked",
                        0
                    ) + 1
                )

            elif action == "require_human_review":

                human_review += 1

                action_counts["human_review"] = (
                    action_counts.get(
                        "human_review",
                        0
                    ) + 1
                )

            else:

                unknown_actions += 1

                action_counts["unknown"] = (
                    action_counts.get(
                        "unknown",
                        0
                    ) + 1
                )

    automated_actions = (
        retry_attempts +
        payment_link_actions
    )

    automated_action_rate = (
        automated_actions / total * 100
        if total else 0
    )

    retry_rate = (
        retry_attempts / total * 100
        if total else 0
    )

    conditional_retry_recovery_rate = (
        expected_retry_recovery /
        retry_value * 100
        if retry_value else 0
    )

    total_automated_value = (
        retry_value +
        payment_link_value
    )

    total_expected_recovery = (
        expected_retry_recovery +
        expected_payment_link_recovery
    )

    conditional_automated_recovery_rate = (
        total_expected_recovery /
        total_automated_value * 100
        if total_automated_value else 0
    )

    return {
        "evaluation_population": total,

        "retry_attempts": retry_attempts,
        "retry_attempt_rate_percent": round(
            retry_rate,
            2
        ),

        "payment_link_actions": payment_link_actions,

        "automated_actions": automated_actions,
        "automated_action_rate_percent": round(
            automated_action_rate,
            2
        ),

        "retry_value": round(
            retry_value,
            2
        ),

        "payment_link_value": round(
            payment_link_value,
            2
        ),

        "total_automated_value": round(
            total_automated_value,
            2
        ),

        "expected_retry_recovery": round(
            expected_retry_recovery,
            2
        ),

        "expected_payment_link_recovery": round(
            expected_payment_link_recovery,
            2
        ),

        "total_expected_recovery": round(
            total_expected_recovery,
            2
        ),

        "conditional_retry_recovery_rate_percent": round(
            conditional_retry_recovery_rate,
            2
        ),

        "conditional_automated_recovery_rate_percent": round(
            conditional_automated_recovery_rate,
            2
        ),

        "human_review": human_review,
        "blocked": blocked,
        "unknown_actions": unknown_actions,

        "action_counts": action_counts
    }


if __name__ == "__main__":

    db = SessionLocal()

    try:

        print("=" * 70)
        print("RecoverAI Operational Metrics")
        print("=" * 70)

        results = run_operational_metrics(
            db,
            held_out_size=500
        )

        print()
        print("Evaluation population:",
              results["evaluation_population"])

        print()
        print("Retry attempts:",
              results["retry_attempts"])

        print("Retry attempt rate:",
              results["retry_attempt_rate_percent"],
              "%")

        print("Payment-link actions:",
              results["payment_link_actions"])

        print("Total automated actions:",
              results["automated_actions"])

        print("Automated action rate:",
              results["automated_action_rate_percent"],
              "%")

        print()
        print("Retry value: ₹",
              results["retry_value"])

        print("Payment-link value: ₹",
              results["payment_link_value"])

        print("Total automated value: ₹",
              results["total_automated_value"])

        print()
        print("Expected recovery from retries: ₹",
              results["expected_retry_recovery"])

        print("Expected recovery from payment links: ₹",
              results["expected_payment_link_recovery"])

        print("Total expected automated recovery: ₹",
              results["total_expected_recovery"])

        print()
        print("Conditional retry recovery rate:",
              results[
                  "conditional_retry_recovery_rate_percent"
              ],
              "%")

        print("Conditional automated recovery rate:",
              results[
                  "conditional_automated_recovery_rate_percent"
              ],
              "%")

        print()
        print("Human review:",
              results["human_review"])

        print("Blocked:",
              results["blocked"])

        print("Unknown actions:",
              results["unknown_actions"])

        print()
        print("Action distribution:")

        for action, count in results[
            "action_counts"
        ].items():

            print(
                f"  {action}: {count}"
            )

        print()
        print("=" * 70)
        print("Read-only operational calculation completed.")
        print("=" * 70)

    finally:

        db.close()