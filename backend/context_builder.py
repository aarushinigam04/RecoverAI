from backend import models


def build_payment_context(payment_id: int, db):
    """
    Build the context required by the AI Diagnosis Agent.

    The context contains:
    - Payment information
    - Customer information
    - Previous payment history
    - Payment attempt history
    - Recovery case history
    - Recovery action history
    """

    # Get the current payment
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.id == payment_id)
        .first()
    )

    if not payment:
        return None

    # Get customer information
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == payment.customer_id)
        .first()
    )

    # Get customer's previous payments
    payment_history = (
        db.query(models.Payment)
        .filter(
            models.Payment.customer_id == payment.customer_id,
            models.Payment.id != payment.id
        )
        .order_by(models.Payment.created_at.desc())
        .all()
    )

    # Get attempts for the current payment
    attempts = (
        db.query(models.PaymentAttempt)
        .filter(models.PaymentAttempt.payment_id == payment.id)
        .order_by(models.PaymentAttempt.attempted_at.desc())
        .all()
    )

    # Get recovery cases for the current payment
    recovery_cases = (
        db.query(models.RecoveryCase)
        .filter(models.RecoveryCase.payment_id == payment.id)
        .order_by(models.RecoveryCase.created_at.desc())
        .all()
    )

    # Get recovery actions associated with those cases
    recovery_actions = []

    for case in recovery_cases:
        actions = (
            db.query(models.RecoveryAction)
            .filter(
                models.RecoveryAction.recovery_case_id == case.id
            )
            .order_by(models.RecoveryAction.created_at.desc())
            .all()
        )

        recovery_actions.extend(actions)

    return {
        "payment": {
            "id": payment.id,
            "customer_id": payment.customer_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "order_id": payment.order_id,
            "failure_reason": payment.failure_reason,
            "created_at": payment.created_at,
        },

        "customer": {
            "id": customer.id if customer else None,
            "name": customer.name if customer else None,
            "email": customer.email if customer else None,
        },

        "payment_history": [
            {
                "id": p.id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "failure_reason": p.failure_reason,
                "created_at": p.created_at,
            }
            for p in payment_history
        ],

        "attempt_history": [
            {
                "id": attempt.id,
                "status": attempt.status,
                "failure_reason": attempt.failure_reason,
                "attempted_at": attempt.attempted_at,
            }
            for attempt in attempts
        ],

        "recovery_history": [
            {
                "id": case.id,
                "status": case.status,
                "priority": case.priority,
                "created_at": case.created_at,
            }
            for case in recovery_cases
        ],

        "recovery_actions": [
            {
                "id": action.id,
                "recovery_case_id": action.recovery_case_id,
                "action_type": action.action_type,
                "message": action.message,
                "status": action.status,
                "created_at": action.created_at,
            }
            for action in recovery_actions
        ],
    }