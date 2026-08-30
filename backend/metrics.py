from backend import models


def calculate_metrics(db):
    """
    Phase 9: Metrics & Evaluation

    Calculates recovery performance using unique payments
    instead of counting repeated attempts as separate recoveries.
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
    # EXECUTED ACTIONS
    # ---------------------------------------------------------

    executed_statuses = {
        "retry_scheduled",
        "waiting_for_funds",
        "customer_action_required",
        "bank_contact_required"
    }

    executed_attempts = [
        attempt
        for attempt in attempts
        if attempt.status in executed_statuses
    ]

    executed_actions = len(executed_attempts)

    # ---------------------------------------------------------
    # UNIQUE PAYMENTS WITH EXECUTED RECOVERY
    # ---------------------------------------------------------

    executed_payment_ids = {
        attempt.payment_id
        for attempt in executed_attempts
    }

    unique_recovered_payments = len(executed_payment_ids)

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
    # RECOVERY RATE
    # ---------------------------------------------------------

    if failed_payments > 0:
        recovery_rate = round(
            (unique_recovered_payments / failed_payments) * 100,
            2
        )

        # Never allow the rate to exceed 100%.
        recovery_rate = min(recovery_rate, 100)

    else:
        recovery_rate = 0

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
            "unique_recovered_payments": unique_recovered_payments,
            "blocked_actions": blocked_actions,
            "human_review_cases": human_review_cases
        },

        "performance": {
            "recovery_rate_percent": recovery_rate,
            "blocked_rate_percent": blocked_rate,
            "human_review_rate_percent": human_review_rate
        }
    }