from backend import models
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy
from backend.action_executor import execute_action
from backend.database import SessionLocal


def run_experiment_execution():

    db = SessionLocal()

    try:

        # ====================================================
        # LOAD ONLY THE ISOLATED EXPERIMENT COHORT
        # ====================================================

        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like(
                    "RECOVERAI-EXP-%"
                ),
                models.Payment.status == "failed"
            )
            .order_by(models.Payment.id)
            .all()
        )

        if not payments:
            print("No failed experiment payments found.")
            return

        total = len(payments)

        # ====================================================
        # COUNTERS
        # ====================================================

        executed = 0
        successful = 0
        failed = 0
        blocked = 0
        human_review = 0
        pending = 0
        unknown = 0

        recovered_amount = 0.0

        # ====================================================
        # HEADER
        # ====================================================

        print()
        print("=" * 70)
        print("RecoverAI Experiment Execution")
        print("=" * 70)

        print(
            f"\nExperiment payments to process: {total}"
        )

        # ====================================================
        # PROCESS EACH EXPERIMENT PAYMENT
        # ====================================================

        for payment in payments:

            # ------------------------------------------------
            # STEP 1: AI DIAGNOSIS
            # ------------------------------------------------

            try:

                payment_context = {
                    "id": payment.id,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "status": payment.status,
                    "failure_reason": payment.failure_reason,
                }

                diagnosis = diagnose_payment(
                    {
                        "payment": payment_context
                    }
                )

            except Exception as e:

                print(
                    f"\nPayment {payment.id}: "
                    f"AI diagnosis failed: {e}"
                )

                unknown += 1
                continue

            if not diagnosis:

                unknown += 1
                continue

            # ------------------------------------------------
            # STEP 2: POLICY ENGINE
            # ------------------------------------------------

            try:

                policy_result = evaluate_policy(
                    payment,
                    diagnosis
                )

            except Exception as e:

                print(
                    f"\nPayment {payment.id}: "
                    f"Policy evaluation failed: {e}"
                )

                unknown += 1
                continue

            if not policy_result:

                unknown += 1
                continue

            policy_decision = policy_result.get(
                "policy_decision",
                "UNKNOWN"
            )

            approved_action = policy_result.get(
                "approved_action",
                "unknown"
            )

            # ------------------------------------------------
            # STEP 3: POLICY BLOCK
            # ------------------------------------------------

            if policy_decision == "BLOCKED":

                blocked += 1
                continue

            # ------------------------------------------------
            # STEP 4: HUMAN REVIEW
            # ------------------------------------------------

            if policy_decision == "NEEDS_HUMAN":

                human_review += 1
                continue

            # ------------------------------------------------
            # STEP 5: EXECUTE APPROVED ACTION
            # ------------------------------------------------

            if policy_decision == "APPROVED":

                try:

                    result = execute_action(
                        payment,
                        approved_action,
                        db
                    )

                except Exception as e:

                    print(
                        f"\nPayment {payment.id}: "
                        f"Action execution failed: {e}"
                    )

                    failed += 1
                    continue

                executed += 1

                recovery_status = result.get(
                    "recovery_status",
                    "UNKNOWN"
                )

                # --------------------------------------------
                # CONFIRMED SUCCESS
                # --------------------------------------------

                if recovery_status == "CONFIRMED_SUCCESS":

                    successful += 1

                    recovered_amount += float(
                        payment.amount
                    )

                # --------------------------------------------
                # FAILED EXECUTION
                # --------------------------------------------

                elif recovery_status == "FAILED":

                    failed += 1

                # --------------------------------------------
                # PENDING CUSTOMER ACTION
                # --------------------------------------------

                elif recovery_status == "PENDING":

                    pending += 1

                # --------------------------------------------
                # UNKNOWN RESULT
                # --------------------------------------------

                else:

                    unknown += 1

            # ------------------------------------------------
            # UNKNOWN POLICY DECISION
            # ------------------------------------------------

            else:

                unknown += 1

        # ====================================================
        # FINAL METRICS
        # ====================================================

        recovery_rate = (
            successful / total * 100
            if total > 0
            else 0
        )

        automated_execution_rate = (
            executed / total * 100
            if total > 0
            else 0
        )

        # ====================================================
        # RESULTS
        # ====================================================

        print()
        print("Execution Results")
        print("-" * 70)

        print(
            f"Experiment payments       : {total}"
        )

        print(
            f"Actions executed          : {executed}"
        )

        print(
            f"Successful recoveries     : {successful}"
        )

        print(
            f"Failed executions         : {failed}"
        )

        print(
            f"Blocked payments          : {blocked}"
        )

        print(
            f"Human review              : {human_review}"
        )

        print(
            f"Pending actions           : {pending}"
        )

        print(
            f"Unknown outcomes         : {unknown}"
        )

        # ====================================================
        # MEASURED EXPERIMENT METRICS
        # ====================================================

        print()
        print("Measured Experiment Metrics")
        print("-" * 70)

        print(
            f"Confirmed recovery rate   : "
            f"{recovery_rate:.2f}%"
        )

        print(
            f"Automated execution rate  : "
            f"{automated_execution_rate:.2f}%"
        )

        print(
            f"Recovered revenue         : "
            f"₹{recovered_amount:,.2f}"
        )

        # ====================================================
        # EXPERIMENT NOTE
        # ====================================================

        print()
        print("=" * 70)
        print("CONTROLLED EXPERIMENT")
        print("=" * 70)

        print(
            "Recovery outcomes are produced by the "
            "controlled Test Mode simulator."
        )

        print(
            "Recovered revenue represents confirmed "
            "successful outcomes in this experiment."
        )

        print(
            "This result does not represent real-world "
            "customer payment behavior."
        )

        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":
    run_experiment_execution()