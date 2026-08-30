from backend import models


def execute_action(payment, action_type, db):
    """
    Phase 6: Action Executor

    Executes a policy-approved recovery action
    using a safe simulated payment environment.
    """

    # ---------------------------------------------------------
    # RETRY PAYMENT
    # ---------------------------------------------------------

    if action_type == "retry_payment":

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="retry_scheduled",
            failure_reason=None
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "action_status": "EXECUTED",
            "action": "retry_payment",
            "attempt_id": attempt.id,
            "message": "Payment retry has been scheduled."
        }

    # ---------------------------------------------------------
    # RETRY AFTER FUNDS ARE ADDED
    # ---------------------------------------------------------

    if action_type == "retry_after_funds_added":

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="waiting_for_funds",
            failure_reason=None
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "action_status": "EXECUTED",
            "action": "retry_after_funds_added",
            "attempt_id": attempt.id,
            "message": "Payment retry is waiting for funds to be added."
        }

    # ---------------------------------------------------------
    # UPDATE PAYMENT METHOD
    # ---------------------------------------------------------

    if action_type == "ask_customer_to_update_payment_method":

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="customer_action_required",
            failure_reason=None
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "action_status": "EXECUTED",
            "action": "ask_customer_to_update_payment_method",
            "attempt_id": attempt.id,
            "message": "Customer has been asked to update their payment method."
        }

    # ---------------------------------------------------------
    # CONTACT BANK
    # ---------------------------------------------------------

    if action_type == "ask_customer_to_contact_bank":

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="bank_contact_required",
            failure_reason=None
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "action_status": "EXECUTED",
            "action": "ask_customer_to_contact_bank",
            "attempt_id": attempt.id,
            "message": "Customer has been asked to contact their bank."
        }

    # ---------------------------------------------------------
    # DO NOT RETRY
    # ---------------------------------------------------------

    if action_type == "do_not_retry":

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="retry_blocked",
            failure_reason=None
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "action_status": "BLOCKED",
            "action": "do_not_retry",
            "attempt_id": attempt.id,
            "message": "Payment retry has been blocked."
        }

    # ---------------------------------------------------------
    # HUMAN REVIEW
    # ---------------------------------------------------------

    if action_type == "require_human_review":

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="human_review_required",
            failure_reason=None
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "action_status": "NEEDS_HUMAN",
            "action": "require_human_review",
            "attempt_id": attempt.id,
            "message": "Payment requires human review before further action."
        }

    # ---------------------------------------------------------
    # UNKNOWN ACTION
    # ---------------------------------------------------------

    return {
        "action_status": "FAILED",
        "action": action_type,
        "message": "Unknown action type."
    }