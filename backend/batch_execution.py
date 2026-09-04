from backend import models
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy
from backend.recovery_executor import execute_recovery
from backend.database import SessionLocal


def run_batch_execution(limit=500):
    """
    Controlled Test Mode batch execution.

    Pipeline:
    Payment
        -> AI Diagnosis
        -> Policy Engine
        -> Approved Recovery Action
        -> Controlled Test Mode Execution

    Safety:
    - Only RecoverAI synthetic cohort payments are considered.
    - Only currently failed payments are executed.
    - Only APPROVED automated actions are executed.
    - BLOCKED and NEEDS_HUMAN payments are never automatically executed.
    - No real customer payment is processed.
    """

    db = SessionLocal()

    try:
        # --------------------------------------------------
        # SELECT FAILED PAYMENTS FROM FIXED COHORT
        # --------------------------------------------------

        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like(
                    "RECOVERAI-ORD-%"
                ),
                models.Payment.status == "failed"
            )
            .order_by(models.Payment.id)
            .limit(limit)
            .all()
        )

        if not payments:
            print("No failed RecoverAI payments available.")
            return

        print("\n" + "=" * 70)
        print("RecoverAI Controlled Batch Execution")
        print("=" * 70)

        print(
            f"\nFailed payments selected : {len(payments)}"
        )

        # --------------------------------------------------
        # COUNTERS
        # --------------------------------------------------

        executed = 0
        confirmed_recoveries = 0
        failed_executions = 0
        blocked = 0
        human_review = 0
        unknown = 0

        recovered_amount = 0.0

        # --------------------------------------------------
        # PROCESS PAYMENTS
        # --------------------------------------------------

        for index, payment in enumerate(payments, start=1):

            print(
                f"\n[{index}/{len(payments)}] "
                f"Payment {payment.id} "
                f"₹{float(payment.amount):.2f}"
            )

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
                unknown += 1
                print("  Diagnosis: UNKNOWN")
                continue

            # --------------------------------------------------
            # STEP 2: POLICY
            # --------------------------------------------------

            policy_result = evaluate_policy(
                payment,
                diagnosis
            )

            if not policy_result:
                unknown += 1
                print("  Policy: UNKNOWN")
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
            # SAFETY GATE
            # --------------------------------------------------

            if policy_decision == "BLOCKED":
                blocked += 1
                print(
                    f"  Policy: BLOCKED "
                    f"({approved_action})"
                )
                continue

            if policy_decision == "NEEDS_HUMAN":
                human_review += 1
                print(
                    f"  Policy: NEEDS_HUMAN "
                    f"({approved_action})"
                )
                continue

            if policy_decision != "APPROVED":
                unknown += 1
                print(
                    f"  Policy: UNKNOWN "
                    f"({policy_decision})"
                )
                continue

            # --------------------------------------------------
            # ONLY AUTOMATED ACTIONS
            # --------------------------------------------------

            if approved_action not in {
                "retry_payment",
                "ask_customer_to_update_payment_method"
            }:
                unknown += 1
                print(
                    f"  Action not eligible: "
                    f"{approved_action}"
                )
                continue

            # --------------------------------------------------
            # EXECUTE RECOVERY
            # --------------------------------------------------

            try:

                execution = execute_recovery(
                    payment,
                    policy_result,
                    db
                )

                execution_data = execution.get(
                    "execution",
                    execution
                )

                execution_status = execution_data.get(
                    "execution_status",
                    execution_data.get(
                        "action_status",
                        "UNKNOWN"
                    )
                )

                recovery_status = execution_data.get(
                    "recovery_status",
                    "UNKNOWN"
                )

                executed += 1

                if (
                    recovery_status
                    == "CONFIRMED_SUCCESS"
                    or execution_status == "EXECUTED"
                    and payment.status == "success"
                ):
                    confirmed_recoveries += 1
                    recovered_amount += float(
                        payment.amount
                    )

                    print(
                        "  Result: CONFIRMED SUCCESS"
                    )

                elif execution_status == "FAILED":
                    failed_executions += 1

                    print(
                        "  Result: EXECUTION FAILED"
                    )

                else:
                    print(
                        f"  Result: {recovery_status}"
                    )

            except Exception as e:

                failed_executions += 1

                print(
                    f"  Execution error: {e}"
                )

        # --------------------------------------------------
        # FINAL METRICS
        # --------------------------------------------------

        total = len(payments)

        observed_recovery_rate = (
            confirmed_recoveries / total * 100
            if total > 0
            else 0
        )

        execution_success_rate = (
            confirmed_recoveries / executed * 100
            if executed > 0
            else 0
        )

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        print("\n" + "=" * 70)
        print("Batch Execution Results")
        print("=" * 70)

        print(
            f"Payments selected          : {total}"
        )

        print(
            f"Actions executed           : {executed}"
        )

        print(
            f"Confirmed recoveries       : "
            f"{confirmed_recoveries}"
        )

        print(
            f"Failed executions         : "
            f"{failed_executions}"
        )

        print(
            f"Blocked by policy         : "
            f"{blocked}"
        )

        print(
            f"Human review required     : "
            f"{human_review}"
        )

        print(
            f"Unknown decisions         : "
            f"{unknown}"
        )

        print(
            f"Recovered amount          : "
            f"₹{recovered_amount:.2f}"
        )

        print(
            f"Observed recovery rate   : "
            f"{observed_recovery_rate:.2f}%"
        )

        print(
            f"Execution success rate   : "
            f"{execution_success_rate:.2f}%"
        )

        print("\n" + "=" * 70)
        print("IMPORTANT")
        print("=" * 70)

        print(
            "This is a controlled synthetic/Test Mode "
            "execution experiment."
        )

        print(
            "The observed recovery rate is measured "
            "from this experiment."
        )

        print(
            "It must not be presented as real-world "
            "customer recovery performance."
        )

        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_batch_execution()