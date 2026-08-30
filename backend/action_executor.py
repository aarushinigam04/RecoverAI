from backend import models
from backend.razorpay_client import create_test_order


def execute_action(payment, action_type, db):
    """
    Phase 8: Razorpay Test Mode Action Executor

    Executes a policy-approved recovery action.

    For retry_payment, a Razorpay Test Mode order is created.
    Other recovery actions are recorded as simulated actions.

    IMPORTANT:
    This project uses Razorpay Test Mode only.
    No real payment is processed.
    """

    # ---------------------------------------------------------
    # RETRY PAYMENT
    # ---------------------------------------------------------

    if action_type == "retry_payment":

        try:
            # Create Razorpay Test Mode order.
            # Amount is supplied in paise.
            order = create_test_order(
                amount=int(payment.amount * 100)
            )

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
                "razorpay_order_id": order["id"],
                "razorpay_order_status": order["status"],
                "amount": order["amount"],
                "currency": order["currency"],
                "message": "Payment retry has been scheduled in Razorpay Test Mode."
            }

        except Exception as e:

            return {
                "action_status": "FAILED",
                "action": "retry_payment",
                "message": "Unable to create Razorpay Test Mode order.",
                "error": str(e)
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