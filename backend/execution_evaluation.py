from backend import models
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy
from backend.database import SessionLocal


def run_execution_evaluation(limit=500):
    """
    Evaluate the RecoverAI decision pipeline on currently failed payments.

    The fixed RecoverAI cohort remains:
        RECOVERAI-ORD-0001 ... RECOVERAI-ORD-0500

    Already-successful payments are counted as recovered outcomes,
    but are NOT sent through the recovery decision pipeline again.

    IMPORTANT:
    This evaluator is read-only.
    It does NOT execute recovery actions.
    It does NOT modify payment records.
    """

    db = SessionLocal()

    try:
        # --------------------------------------------------
        # FIXED RECOVERAI EVALUATION COHORT
        # --------------------------------------------------

        cohort = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like("RECOVERAI-ORD-%")
            )
            .order_by(models.Payment.id)
            .limit(limit)
            .all()
        )

        if not cohort:
            print("No RecoverAI evaluation payments found.")
            return

        # --------------------------------------------------
        # PAYMENT STATUS COUNTERS
        # --------------------------------------------------

        successful_payments = sum(
            1 for payment in cohort
            if payment.status == "success"
        )

        failed_payments = sum(
            1 for payment in cohort
            if payment.status == "failed"
        )

        # --------------------------------------------------
        # ONLY CURRENTLY FAILED PAYMENTS NEED A NEW
        # RECOVERY DECISION
        # --------------------------------------------------

        payments = [
            payment
            for payment in cohort
            if payment.status == "failed"
        ]

        # --------------------------------------------------
        # COUNTERS
        # --------------------------------------------------

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

        print("\n" + "=" * 70)
        print("RecoverAI Execution Evaluation")
        print("=" * 70)

        print(
            f"\nFixed evaluation cohort : {len(cohort)} payments"
        )

        print(
            f"Currently successful     : {successful_payments}"
        )

        print(
            f"Currently failed        : {failed_payments}"
        )

        print(
            f"Decision evaluation set : {len(payments)} failed payments"
        )

        # --------------------------------------------------
        # EVALUATE CURRENTLY FAILED PAYMENTS ONLY
        # --------------------------------------------------

        for payment in payments:

            payment_context = {
                "id": payment.id,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "failure_reason": payment.failure_reason,
            }

            # --------------------------------------------------
            # STEP 1: AI DIAGNOSIS
            # --------------------------------------------------

            diagnosis = diagnose_payment(
                {
                    "payment": payment_context
                }
            )

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

            confidence_values.append(confidence)

            # --------------------------------------------------
            # STEP 2: POLICY ENGINE
            # --------------------------------------------------

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

            # --------------------------------------------------
            # POLICY COUNTERS
            # --------------------------------------------------

            if policy_decision == "APPROVED":
                policy_approved += 1

            elif policy_decision == "BLOCKED":
                policy_blocked += 1

            elif policy_decision == "NEEDS_HUMAN":
                policy_human_review += 1

            # --------------------------------------------------
            # FINAL ACTION
            # --------------------------------------------------

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

            # --------------------------------------------------
            # AUTOMATED OPPORTUNITIES
            # --------------------------------------------------

            if (
                policy_decision == "APPROVED"
                and approved_action in {
                    "retry_payment",
                    "ask_customer_to_update_payment_method"
                }
            ):
                automated_opportunities += 1

        # ------------------------------------------------------
        # METRICS
        # ------------------------------------------------------

        decision_total = len(payments)

        automated_action_rate = (
            automated_opportunities / decision_total * 100
            if decision_total > 0
            else 0
        )

        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
            * 100
            if confidence_values
            else 0
        )

        # ------------------------------------------------------
        # OUTPUT
        # ------------------------------------------------------

        print("\nEvaluation Results")
        print("-" * 65)

        print(
            f"Fixed cohort             : {len(cohort)}"
        )

        print(
            f"Currently successful     : {successful_payments}"
        )

        print(
            f"Currently failed        : {failed_payments}"
        )

        print(
            f"Payments needing decision: {decision_total}"
        )

        print(
            f"Retry payment actions    : {retry_actions}"
        )

        print(
            f"Payment-link actions     : {payment_link_actions}"
        )

        print(
            f"Stopped actions          : {stopped_actions}"
        )

        print(
            f"Human review             : {human_review_actions}"
        )

        print(
            f"Unknown actions          : {unknown_actions}"
        )

        print("\nPolicy Safety")
        print("-" * 65)

        print(
            f"Policy approved          : {policy_approved}"
        )

        print(
            f"Policy blocked           : {policy_blocked}"
        )

        print(
            f"Policy human review      : {policy_human_review}"
        )

        print("\nDecision Metrics")
        print("-" * 65)

        print(
            f"Automated recovery opportunities : "
            f"{automated_opportunities}"
        )

        print(
            f"Automated action rate            : "
            f"{automated_action_rate:.2f}%"
        )

        print(
            f"Average AI confidence            : "
            f"{average_confidence:.2f}%"
        )

        # ------------------------------------------------------
        # EVALUATION NOTE
        # ------------------------------------------------------

        print("\n" + "=" * 70)
        print("IMPORTANT")
        print("=" * 70)

        print(
            "The fixed cohort contains both successful and failed "
            "payments."
        )

        print(
            "Already-successful payments are counted as observed "
            "recovery outcomes."
        )

        print(
            "Only currently failed payments are evaluated for a "
            "new recovery decision."
        )

        print(
            "This evaluator is read-only and does not execute "
            "recovery actions."
        )

        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_execution_evaluation()