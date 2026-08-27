def get_recovery_recommendation(payment):
    if payment.status == "failed":
        return {
            "action": "retry_payment",
            "message": "Payment failed. Customer can retry the payment."
        }

    return {
        "action": "no_action",
        "message": "No recovery action required."
    }