from backend import models


def execute_recovery(payment, policy_result, db):
    """
    Execute a recovery action only after it has been
    approved by the Policy & Safety Engine.

    Phase 5:
    Also records the recovery action in the database.
    """

    policy_decision = policy_result["policy_decision"]
    approved_action = policy_result["approved_action"]

    # ---------------------------------------------------------
    # Find or create a recovery case
    # ---------------------------------------------------------

    recovery_case = (
        db.query(models.RecoveryCase)
        .filter(models.RecoveryCase.payment_id == payment.id)
        .order_by(models.RecoveryCase.created_at.desc())
        .first()
    )

    if not recovery_case:
        recovery_case = models.RecoveryCase(
            payment_id=payment.id,
            status="open",
            priority="medium"
        )

        db.add(recovery_case)
        db.commit()
        db.refresh(recovery_case)

    # ---------------------------------------------------------
    # BLOCKED
    # ---------------------------------------------------------

    if policy_decision == "BLOCKED":

        action = models.RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type="do_not_retry",
            message="Recovery action was blocked by the policy engine.",
            status="blocked"
        )

        db.add(action)
        db.commit()

        return {
            "execution_status": "BLOCKED",
            "action": "do_not_retry",
            "message": "Recovery action was blocked by the policy engine."
        }

    # ---------------------------------------------------------
    # NEEDS HUMAN
    # ---------------------------------------------------------

    if policy_decision == "NEEDS_HUMAN":

        action = models.RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type="require_human_review",
            message="Recovery action requires human review.",
            status="needs_human"
        )

        db.add(action)
        db.commit()

        return {
            "execution_status": "NEEDS_HUMAN",
            "action": "require_human_review",
            "message": "Recovery action requires human review."
        }

    # ---------------------------------------------------------
    # APPROVED
    # ---------------------------------------------------------

    if policy_decision == "APPROVED":

        # Retry payment
        if approved_action == "retry_payment":

            message = "Payment retry action has been scheduled."

        # Retry after customer adds funds
        elif approved_action == "retry_after_funds_added":

            message = "Payment retry will occur after funds are added."

        # Ask customer to update payment method
        elif approved_action == "ask_customer_to_update_payment_method":

            message = "Customer should update their payment method."

        # Ask customer to contact bank
        elif approved_action == "ask_customer_to_contact_bank":

            message = "Customer should contact their bank."

        # Do not retry
        elif approved_action == "do_not_retry":

            message = "No payment retry will be performed."

        # Unknown action
        else:

            action = models.RecoveryAction(
                recovery_case_id=recovery_case.id,
                action_type=approved_action,
                message="Unknown recovery action.",
                status="failed"
            )

            db.add(action)
            db.commit()

            return {
                "execution_status": "FAILED",
                "action": approved_action,
                "message": "Unknown recovery action."
            }

        # -----------------------------------------------------
        # Save approved action
        # -----------------------------------------------------

        action = models.RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=approved_action,
            message=message,
            status="executed"
        )

        db.add(action)
        db.commit()

        return {
            "execution_status": "EXECUTED",
            "action": approved_action,
            "message": message
        }

    # ---------------------------------------------------------
    # UNKNOWN POLICY DECISION
    # ---------------------------------------------------------

    action = models.RecoveryAction(
        recovery_case_id=recovery_case.id,
        action_type=approved_action,
        message="Unknown policy decision.",
        status="failed"
    )

    db.add(action)
    db.commit()

    return {
        "execution_status": "FAILED",
        "action": approved_action,
        "message": "Unknown policy decision."
    }