from backend import models


def calculate_metrics(db):
    """
    Phase 9/12: Metrics & Evaluation

    Calculates confirmed recovery metrics only for the
    original RecoverAI synthetic evaluation cohort.

    The seed dataset creates 500 evaluation payments with
    order IDs:

        RECOVERAI-ORD-0001
        ...
        RECOVERAI-ORD-0500

    The cohort remains fixed even after a payment changes
    from failed -> success.

    Payment.status is the source of truth for confirmed
    recovery.
    """

    # =========================================================
    # ORIGINAL SYNTHETIC EVALUATION COHORT
    # =========================================================
    #
    # IMPORTANT:
    # Do NOT calculate metrics from every payment in the
    # database because additional test payments may exist.
    #

    evaluation_payments = (
        db.query(models.Payment)
        .filter(
            models.Payment.order_id.like("RECOVERAI-ORD-%")
        )
        .all()
    )

    evaluation_payment_ids = {
        payment.id
        for payment in evaluation_payments
    }

    # ---------------------------------------------------------
    # PAYMENT STATISTICS
    # ---------------------------------------------------------

    total_payments = len(evaluation_payments)

    failed_payments = sum(
        1
        for payment in evaluation_payments
        if payment.status == "failed"
    )

    successful_payments = sum(
        1
        for payment in evaluation_payments
        if payment.status == "success"
    )

    # ---------------------------------------------------------
    # PAYMENT ATTEMPTS
    # ---------------------------------------------------------
    #
    # Only attempts belonging to the original evaluation
    # cohort are included.
    #

    if evaluation_payment_ids:

        attempts = (
            db.query(models.PaymentAttempt)
            .filter(
                models.PaymentAttempt.payment_id.in_(
                    evaluation_payment_ids
                )
            )
            .all()
        )

    else:

        attempts = []

    total_attempts = len(attempts)

    # ---------------------------------------------------------
    # CONFIRMED RECOVERIES
    # ---------------------------------------------------------
    #
    # Payment.status is the source of truth.
    #
    # A successful PaymentAttempt alone does NOT count as
    # a confirmed recovery.
    #

    confirmed_recovered_payment_ids = {
        payment.id
        for payment in evaluation_payments
        if payment.status == "success"
    }

    confirmed_recovered_payments = len(
        confirmed_recovered_payment_ids
    )

    # ---------------------------------------------------------
    # EXECUTED ACTIONS
    # ---------------------------------------------------------

    executed_statuses = {
        "retry_scheduled",
        "waiting_for_funds",
        "customer_action_required",
        "bank_contact_required",
        "success"
    }

    executed_actions = sum(
        1
        for attempt in attempts
        if attempt.status in executed_statuses
    )

    # ---------------------------------------------------------
    # BLOCKED ACTIONS
    # ---------------------------------------------------------

    blocked_actions = sum(
        1
        for attempt in attempts
        if attempt.status == "retry_blocked"
    )

    # ---------------------------------------------------------
    # HUMAN REVIEW CASES
    # ---------------------------------------------------------

    human_review_cases = sum(
        1
        for attempt in attempts
        if attempt.status == "human_review_required"
    )

    # ---------------------------------------------------------
    # CONFIRMED PAYMENT RECOVERY RATE
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    #
    # The denominator is the ORIGINAL evaluation cohort,
    # not the number of payments that are currently failed.
    #
    # Therefore, if 1 of the original 500 payments is recovered:
    #
    #     1 / 500 * 100 = 0.20%
    #
    # If 3 are recovered:
    #
    #     3 / 500 * 100 = 0.60%
    #

    original_failed_payment_population = total_payments

    if original_failed_payment_population > 0:

        confirmed_recovery_rate = round(
            (
                confirmed_recovered_payments
                / original_failed_payment_population
            ) * 100,
            2
        )

        # Safety protection.
        confirmed_recovery_rate = min(
            confirmed_recovery_rate,
            100
        )

    else:

        confirmed_recovery_rate = 0

    # ---------------------------------------------------------
    # BLOCK RATE
    # ---------------------------------------------------------

    if total_attempts > 0:

        blocked_rate = round(
            (
                blocked_actions
                / total_attempts
            ) * 100,
            2
        )

    else:

        blocked_rate = 0

    # ---------------------------------------------------------
    # HUMAN REVIEW RATE
    # ---------------------------------------------------------

    if total_attempts > 0:

        human_review_rate = round(
            (
                human_review_cases
                / total_attempts
            ) * 100,
            2
        )

    else:

        human_review_rate = 0

    # ---------------------------------------------------------
    # RETURN METRICS
    # ---------------------------------------------------------

    return {

        "payments": {
            "total": total_payments,
            "failed": failed_payments,
            "successful": successful_payments
        },

        "recovery": {
            "total_attempts": total_attempts,
            "executed_actions": executed_actions,
            "confirmed_recovered_payments": (
                confirmed_recovered_payments
            ),
            "blocked_actions": blocked_actions,
            "human_review_cases": human_review_cases
        },

        "performance": {
            "confirmed_recovery_rate_percent": (
                confirmed_recovery_rate
            ),
            "blocked_rate_percent": blocked_rate,
            "human_review_rate_percent": human_review_rate
        }
    }