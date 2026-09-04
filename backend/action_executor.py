import random

from backend import models
from backend.razorpay_client import create_test_order


# ============================================================
# CONTROLLED TEST OUTCOME MODEL
# ============================================================

TEST_OUTCOME_MODEL = {

    "insufficient funds": {
        "retry_payment": 0.10,
        "payment_link": 0.65
    },

    "card expired": {
        "retry_payment": 0.10,
        "payment_link": 0.65
    },

    "bank timeout": {
        "retry_payment": 0.80,
        "payment_link": 0.40
    },

    "gateway timeout": {
        "retry_payment": 0.80,
        "payment_link": 0.40
    },

    "payment api unavailable": {
        "retry_payment": 0.80,
        "payment_link": 0.40
    },

    "network timeout": {
        "retry_payment": 0.80,
        "payment_link": 0.40
    },

    "network connectivity issue": {
        "retry_payment": 0.80,
        "payment_link": 0.40
    }
}


def normalize_reason(reason):

    if not reason:
        return ""

    return reason.strip().lower()


def get_failure_category(payment):

    reason = normalize_reason(
        payment.failure_reason
    )

    if "insufficient funds" in reason:
        return "insufficient funds"

    if "card expired" in reason:
        return "card expired"

    if "bank timeout" in reason:
        return "bank timeout"

    if "gateway timeout" in reason:
        return "gateway timeout"

    if "payment api unavailable" in reason:
        return "payment api unavailable"

    if "network timeout" in reason:
        return "network timeout"

    if "network connectivity" in reason:
        return "network connectivity issue"

    if "payment declined" in reason:
        return "payment declined"

    if "invalid payment details" in reason:
        return "invalid payment details"

    if "customer opted out" in reason:
        return "customer opted out"

    if "retry limit exceeded" in reason:
        return "retry limit exceeded"

    if "llm timeout" in reason:
        return "llm timeout"

    if "duplicate webhook" in reason:
        return "duplicate webhook"

    if "fraud detected" in reason:
        return "fraud detected"

    if "payment already captured" in reason:
        return "payment already captured"

    return None


def get_test_success_probability(
    payment,
    action_type
):

    category = get_failure_category(payment)

    if not category:
        return 0.0

    # --------------------------------------------------------
    # RETRY PAYMENT
    # --------------------------------------------------------

    if action_type == "retry_payment":

        outcome = TEST_OUTCOME_MODEL.get(category)

        if not outcome:
            return 0.0

        return outcome.get(
            "retry_payment",
            0.0
        )

    # --------------------------------------------------------
    # PAYMENT LINK
    # --------------------------------------------------------

    if action_type == "ask_customer_to_update_payment_method":

        outcome = TEST_OUTCOME_MODEL.get(category)

        if not outcome:
            return 0.0

        return outcome.get(
            "payment_link",
            0.0
        )

    return 0.0


def simulate_test_outcome(
    payment,
    action_type,
    success_probability
):
    """
    Reproducible synthetic outcome simulator.

    The predefined success probability is preserved.

    Payment ID + action type create a stable deterministic
    seed so repeated simulations produce the same result.

    This is a controlled synthetic/Test Mode simulation.
    It does not represent real customer payment behavior.
    """

    if success_probability <= 0:
        return False

    if success_probability >= 1:
        return True

    seed_value = (
        f"RecoverAI:{payment.id}:{action_type}"
    )

    rng = random.Random(seed_value)

    random_value = rng.random()

    return random_value < success_probability


# ============================================================
# ACTION EXECUTOR
# ============================================================

def execute_action(
    payment,
    action_type,
    db
):

    """
    Phase 8: Razorpay Test Mode Action Executor.

    Executes a policy-approved recovery action.

    All payment recovery outcomes in this controlled
    implementation are synthetic/Test Mode outcomes.

    No real customer payment is processed.
    """

    # ========================================================
    # RETRY PAYMENT
    # ========================================================

    if action_type == "retry_payment":

        try:

            # ------------------------------------------------
            # Create Razorpay Test Mode order
            # ------------------------------------------------

            order = create_test_order(
                amount=int(
                    payment.amount * 100
                )
            )

            # ------------------------------------------------
            # Determine controlled success probability
            # ------------------------------------------------

            success_probability = (
                get_test_success_probability(
                    payment,
                    "retry_payment"
                )
            )

            # ------------------------------------------------
            # Reproducible probability-based outcome
            # ------------------------------------------------

            recovered = simulate_test_outcome(
                payment,
                "retry_payment",
                success_probability
            )

            # ------------------------------------------------
            # CONFIRMED SUCCESS
            # ------------------------------------------------

            if recovered:

                payment.status = "success"
                payment.failure_reason = None

                attempt = models.PaymentAttempt(
                    payment_id=payment.id,
                    status="success",
                    failure_reason=None
                )

                db.add(attempt)
                db.commit()
                db.refresh(attempt)

                return {

                    "action_status":
                        "EXECUTED",

                    "recovery_status":
                        "CONFIRMED_SUCCESS",

                    "action":
                        "retry_payment",

                    "attempt_id":
                        attempt.id,

                    "razorpay_order_id":
                        order["id"],

                    "razorpay_order_status":
                        order["status"],

                    "amount":
                        order["amount"],

                    "currency":
                        order["currency"],

                    "success_probability":
                        success_probability,

                    "message": (
                        "Controlled Test Mode recovery "
                        "outcome was successful."
                    )
                }

            # ------------------------------------------------
            # CONTROLLED FAILED OUTCOME
            # ------------------------------------------------

            attempt = models.PaymentAttempt(
                payment_id=payment.id,
                status="failed",
                failure_reason=payment.failure_reason
            )

            db.add(attempt)
            db.commit()
            db.refresh(attempt)

            return {

                "action_status":
                    "EXECUTED",

                "recovery_status":
                    "FAILED",

                "action":
                    "retry_payment",

                "attempt_id":
                    attempt.id,

                "razorpay_order_id":
                    order["id"],

                "razorpay_order_status":
                    order["status"],

                "amount":
                    order["amount"],

                "currency":
                    order["currency"],

                "success_probability":
                    success_probability,

                "message": (
                    "Controlled Test Mode recovery "
                    "outcome was unsuccessful."
                )
            }

        except Exception as e:

            return {

                "action_status":
                    "FAILED",

                "recovery_status":
                    "FAILED",

                "action":
                    "retry_payment",

                "message":
                    f"Unable to execute Test Mode retry: {str(e)}",

                "error":
                    str(e)
            }

    # ========================================================
    # RETRY AFTER FUNDS ARE ADDED
    # ========================================================

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

            "action_status":
                "EXECUTED",

            "recovery_status":
                "PENDING",

            "action":
                "retry_after_funds_added",

            "attempt_id":
                attempt.id,

            "message":
                "Payment retry is waiting for funds to be added."
        }

    # ========================================================
    # UPDATE PAYMENT METHOD
    # ========================================================

    if action_type == (
        "ask_customer_to_update_payment_method"
    ):

        # ----------------------------------------------------
        # Determine controlled Test Mode success probability
        # ----------------------------------------------------

        success_probability = (
            get_test_success_probability(
                payment,
                "ask_customer_to_update_payment_method"
            )
        )

        # ----------------------------------------------------
        # Reproducible synthetic outcome
        # ----------------------------------------------------

        recovered = simulate_test_outcome(
            payment,
            "ask_customer_to_update_payment_method",
            success_probability
        )

        # ----------------------------------------------------
        # CONFIRMED SUCCESS
        # ----------------------------------------------------

        if recovered:

            payment.status = "success"
            payment.failure_reason = None

            attempt = models.PaymentAttempt(
                payment_id=payment.id,
                status="success",
                failure_reason=None
            )

            db.add(attempt)
            db.commit()
            db.refresh(attempt)

            return {

                "action_status":
                    "EXECUTED",

                "recovery_status":
                    "CONFIRMED_SUCCESS",

                "action":
                    "ask_customer_to_update_payment_method",

                "attempt_id":
                    attempt.id,

                "success_probability":
                    success_probability,

                "message":
                    "Controlled Test Mode payment-method "
                    "update resulted in successful recovery."
            }

        # ----------------------------------------------------
        # CONTROLLED FAILED OUTCOME
        # ----------------------------------------------------

        attempt = models.PaymentAttempt(
            payment_id=payment.id,
            status="failed",
            failure_reason=payment.failure_reason
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {

            "action_status":
                "EXECUTED",

            "recovery_status":
                "FAILED",

            "action":
                "ask_customer_to_update_payment_method",

            "attempt_id":
                attempt.id,

            "success_probability":
                success_probability,

            "message":
                "Controlled Test Mode payment-method "
                "update did not recover the payment."
        }

    # ========================================================
    # CONTACT BANK
    # ========================================================

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

            "action_status":
                "EXECUTED",

            "recovery_status":
                "PENDING",

            "action":
                "ask_customer_to_contact_bank",

            "attempt_id":
                attempt.id,

            "message":
                "Customer has been asked to contact their bank."
        }

    # ========================================================
    # DO NOT RETRY
    # ========================================================

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

            "action_status":
                "BLOCKED",

            "recovery_status":
                "BLOCKED",

            "action":
                "do_not_retry",

            "attempt_id":
                attempt.id,

            "message":
                "Payment retry has been blocked."
        }

    # ========================================================
    # HUMAN REVIEW
    # ========================================================

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

            "action_status":
                "NEEDS_HUMAN",

            "recovery_status":
                "NEEDS_HUMAN",

            "action":
                "require_human_review",

            "attempt_id":
                attempt.id,

            "message":
                "Payment requires human review before further action."
        }

    # ========================================================
    # UNKNOWN ACTION
    # ========================================================

    return {

        "action_status":
            "FAILED",

        "recovery_status":
            "FAILED",

        "action":
            action_type,

        "message":
            "Unknown action type."
    }