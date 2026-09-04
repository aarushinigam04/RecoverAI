from backend import models
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy
from backend.action_executor import execute_action
from backend.database import SessionLocal


def run_customer_action_experiment():

    db = SessionLocal()

    try:

        # Find only experiment payments that are still pending
        # after the first experiment execution.
        payments = (
            db.query(models.Payment)
            .filter(
                models.Payment.order_id.like("RECOVERAI-EXP-%"),
                models.Payment.status == "failed"
            )
            .order_by(models.Payment.id)
            .all()
        )

        # Keep only payments whose latest attempt requires
        # customer action.
        pending_payments = []

        for payment in payments:

            attempts = (
                db.query(models.PaymentAttempt)
                .filter(
                    models.PaymentAttempt.payment_id == payment.id
                )
                .order_by(models.PaymentAttempt.id)
                .all()
            )

            if not attempts:
                continue

            latest_attempt = attempts[-1]

            if latest_attempt.status == "customer_action_required":
                pending_payments.append(payment)

        if not pending_payments:
            print("No pending customer-action payments found.")
            return

        total = len(pending_payments)

        customer_completed = 0
        retry_executed = 0
        successful = 0
        failed = 0
        still_pending = 0

        recovered_amount = 0.0

        print()
        print("=" * 80)
        print("RecoverAI Customer-Action Recovery Experiment")
        print("=" * 80)

        print()
        print(
            f"Pending customer-action payments: {total}"
        )

        # ---------------------------------------------------------
        # Process each pending customer-action payment
        # ---------------------------------------------------------

        for payment in pending_payments:

            try:

                # -------------------------------------------------
                # STEP 1
                # Simulate customer completing the requested action
                # -------------------------------------------------

                customer_completed += 1

                print(
                    f"\nPayment {payment.id} "
                    f"| Customer action completed"
                )

                # -------------------------------------------------
                # STEP 2
                # Re-run AI diagnosis using current payment context
                # -------------------------------------------------

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

                if not diagnosis:
                    still_pending += 1
                    print(
                        f"Payment {payment.id} "
                        f"| Diagnosis unavailable"
                    )
                    continue

                # -------------------------------------------------
                # STEP 3
                # Evaluate policy
                # -------------------------------------------------

                policy_result = evaluate_policy(
                    payment,
                    diagnosis
                )

                if not policy_result:
                    still_pending += 1
                    print(
                        f"Payment {payment.id} "
                        f"| Policy result unavailable"
                    )
                    continue

                policy_decision = policy_result.get(
                    "policy_decision",
                    "UNKNOWN"
                )

                approved_action = policy_result.get(
                    "approved_action",
                    "unknown"
                )

                # -------------------------------------------------
                # STEP 4
                # Only retry if policy approves the retry
                # -------------------------------------------------

                if policy_decision != "APPROVED":
                    still_pending += 1

                    print(
                        f"Payment {payment.id} "
                        f"| Policy: {policy_decision}"
                    )

                    continue

                # Customer has updated/completed the payment action.
                # The next recovery step is a controlled retry.
                retry_action = "retry_payment"

                result = execute_action(
                    payment,
                    retry_action,
                    db
                )

                retry_executed += 1

                recovery_status = result.get(
                    "recovery_status",
                    "UNKNOWN"
                )

                if recovery_status == "CONFIRMED_SUCCESS":

                    successful += 1

                    recovered_amount += float(
                        payment.amount
                    )

                    print(
                        f"Payment {payment.id} "
                        f"| RETRY SUCCESS "
                        f"| ₹{float(payment.amount):,.2f}"
                    )

                elif recovery_status == "FAILED":

                    failed += 1

                    print(
                        f"Payment {payment.id} "
                        f"| RETRY FAILED"
                    )

                elif recovery_status == "PENDING":

                    still_pending += 1

                    print(
                        f"Payment {payment.id} "
                        f"| RETRY PENDING"
                    )

                else:

                    still_pending += 1

                    print(
                        f"Payment {payment.id} "
                        f"| UNKNOWN OUTCOME"
                    )

            except Exception as e:

                failed += 1

                print(
                    f"Payment {payment.id} "
                    f"| ERROR: {e}"
                )

        # ---------------------------------------------------------
        # Metrics
        # ---------------------------------------------------------

        additional_recovery_rate = (
            successful / total * 100
            if total > 0
            else 0
        )

        customer_completion_rate = (
            customer_completed / total * 100
            if total > 0
            else 0
        )

        retry_execution_rate = (
            retry_executed / total * 100
            if total > 0
            else 0
        )

        # Original experiment had 30 successful recoveries.
        original_successes = 30

        final_successes = original_successes + successful

        final_recovery_rate = (
            final_successes / 100 * 100
        )

        print()
        print("=" * 80)
        print("CUSTOMER-ACTION EXPERIMENT RESULTS")
        print("=" * 80)

        print()
        print(
            f"Pending payments processed : {total}"
        )

        print(
            f"Customer actions completed : "
            f"{customer_completed}"
        )

        print(
            f"Retries executed           : "
            f"{retry_executed}"
        )

        print(
            f"Additional successes       : "
            f"{successful}"
        )

        print(
            f"Additional failures        : "
            f"{failed}"
        )

        print(
            f"Still pending              : "
            f"{still_pending}"
        )

        print()
        print("Metrics")
        print("-" * 80)

        print(
            f"Customer completion rate   : "
            f"{customer_completion_rate:.2f}%"
        )

        print(
            f"Retry execution rate       : "
            f"{retry_execution_rate:.2f}%"
        )

        print(
            f"Additional recovery rate   : "
            f"{additional_recovery_rate:.2f}%"
        )

        print(
            f"Additional revenue         : "
            f"₹{recovered_amount:,.2f}"
        )

        print()
        print(
            f"Original recoveries        : "
            f"{original_successes}"
        )

        print(
            f"Additional recoveries      : "
            f"{successful}"
        )

        print(
            f"Final recoveries           : "
            f"{final_successes}"
        )

        print(
            f"Final recovery rate        : "
            f"{final_recovery_rate:.2f}%"
        )

        print()
        print("=" * 80)
        print("CONTROLLED EXPERIMENT")
        print("=" * 80)

        print(
            "Customer completion is simulated."
        )

        print(
            "Retry outcomes are produced by the "
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

        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_customer_action_experiment()