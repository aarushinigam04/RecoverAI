from backend import models
from backend.action_executor import execute_action


def execute_recovery(payment, policy_result, db):
    """
    Execute a recovery action only after it has been
    approved by the Policy & Safety Engine.

    Records the recovery action and delegates approved
    actions to the Action Executor.
    """

    policy_decision = policy_result["policy_decision"]
    approved_action = policy_result["approved_action"]

    # ---------------------------------------------------------
    # Find or create recovery case
    # ---------------------------------------------------------

    recovery_case = (
        db.query(models.RecoveryCase)
        .filter(
            models.RecoveryCase.payment_id == payment.id
        )
        .order_by(
            models.RecoveryCase.created_at.desc()
        )
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
        action_result = execute_action(
            payment=payment,
            action_type=approved_action,
            db=db
        )

        action = models.RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=approved_action,
            message=action_result["message"],
            status="blocked"
       )

        db.add(action)
        db.commit()

        return {
            "execution_status": "BLOCKED",
            "action": approved_action,
            "message": action_result["message"],
            "attempt_id": action_result.get("attempt_id")
        }

    # ---------------------------------------------------------
    # NEEDS HUMAN
    # ---------------------------------------------------------

    if policy_decision == "NEEDS_HUMAN":
        
        action_result = execute_action(
            payment=payment,
            action_type=approved_action,
            db=db
        )

        action = models.RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=approved_action,
            message=action_result["message"],
            status="needs_human"
     )

        db.add(action)
        db.commit()

        return {
            "execution_status": "NEEDS_HUMAN",
            "action": approved_action,
            "message": action_result["message"],
            "attempt_id": action_result.get("attempt_id")
       }

    # ---------------------------------------------------------
    # APPROVED
    # ---------------------------------------------------------

    if policy_decision == "APPROVED":

        # Execute the policy-approved action
        action_result = execute_action(
            payment=payment,
            action_type=approved_action,
            db=db
        )

        # -----------------------------------------------------
        # Determine RecoveryAction status
        # -----------------------------------------------------

        if action_result["action_status"] == "EXECUTED":
            recovery_action_status = "executed"

        elif action_result["action_status"] == "BLOCKED":
            recovery_action_status = "blocked"

        elif action_result["action_status"] == "NEEDS_HUMAN":
            recovery_action_status = "needs_human"

        else:
            recovery_action_status = "failed"

        # -----------------------------------------------------
        # Record action in recovery_actions table
        # -----------------------------------------------------

        action = models.RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=approved_action,
            message=action_result["message"],
            status=recovery_action_status
        )

        db.add(action)
        db.commit()

        # -----------------------------------------------------
        # Return execution result
        # -----------------------------------------------------

        return {
            "execution_status": action_result["action_status"],
            "action": approved_action,
            "message": action_result["message"],
            "attempt_id": action_result.get("attempt_id")
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