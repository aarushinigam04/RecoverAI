from backend import models


def calculate_metrics(db):
    """
    Phase 9/12: Metrics & Evaluation

    Calculates confirmed payment recovery metrics.

    A payment is considered successfully recovered only when
    the actual Payment record has status = "success".

    Repeated payment attempts for the same payment are counted
    only once when calculating confirmed recoveries.
    """

    # ---------------------------------------------------------
    # PAYMENT STATISTICS
    # ---------------------------------------------------------

    total_payments = db.query(models.Payment).count()

    failed_payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "failed")
        .count()
    )

    successful_payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "success")
        .count()
    )

    # ---------------------------------------------------------
    # PAYMENT ATTEMPTS
    # ---------------------------------------------------------

    attempts = db.query(models.PaymentAttempt).all()

    total_attempts = len(attempts)

    # ---------------------------------------------------------
    # CONFIRMED RECOVERIES
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # We use Payment.status as the source of truth.
    #
    # A "success" PaymentAttempt alone does NOT mean the
    # payment was successfully recovered.
    #

    confirmed_recovered_payment_ids = {
        payment.id
        for payment in db.query(models.Payment).all()
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
    # Current failed payments + confirmed recovered payments
    # represents the original failed-payment population.
    #
    # Example:
    #
    # 1 confirmed recovery
    # 14 currently failed
    #
    # Original failed population = 1 + 14 = 15
    #
    # Recovery rate = 1 / 15 * 100 = 6.67%
    #

    original_failed_payment_population = (
        confirmed_recovered_payments
        + failed_payments
    )

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
            (blocked_actions / total_attempts) * 100,
            2
        )

    else:
        blocked_rate = 0

    # ---------------------------------------------------------
    # HUMAN REVIEW RATE
    # ---------------------------------------------------------

    if total_attempts > 0:

        human_review_rate = round(
            (human_review_cases / total_attempts) * 100,
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