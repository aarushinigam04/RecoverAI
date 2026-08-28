def get_recovery_recommendation(payment):
    failure_reason = (payment.failure_reason or "").lower()

    if "insufficient" in failure_reason or "balance" in failure_reason:
        return {
            "failure_category": "Insufficient Funds",
            "recommendation": "Ask the customer to add funds and retry the payment."
        }

    elif "timeout" in failure_reason or "timed out" in failure_reason:
        return {
            "failure_category": "Payment Timeout",
            "recommendation": "Ask the customer to retry the payment after a short wait."
        }

    elif "invalid" in failure_reason:
        return {
            "failure_category": "Invalid Payment Details",
            "recommendation": "Ask the customer to verify the payment details and try again."
        }

    elif "high-value" in failure_reason or "approval" in failure_reason:
        return {
            "failure_category": "High-Value Payment",
            "recommendation": "Route the payment for approval before retrying."
        }

    elif "declined" in failure_reason or "decline" in failure_reason:
        return {
            "failure_category": "Bank Declined",
            "recommendation": "Ask the customer to contact their bank or use another payment method."
        }

    elif "card expired" in failure_reason or "expired" in failure_reason:
        return {
            "failure_category": "Expired Card",
            "recommendation": "Ask the customer to update their card details or use another card."
        }

    elif "duplicate webhook" in failure_reason:
        return {
            "failure_category": "Duplicate Webhook",
            "recommendation": "Ignore the duplicate webhook and keep the original payment record."
        }

    elif "api unavailable" in failure_reason:
        return {
            "failure_category": "Payment Service Unavailable",
            "recommendation": "Retry the payment after the payment service becomes available."
        }

    elif "already captured" in failure_reason:
        return {
            "failure_category": "Payment Already Captured",
            "recommendation": "Do not retry the payment. Verify the existing captured payment."
        }

    elif "retry limit" in failure_reason:
        return {
            "failure_category": "Retry Limit Exceeded",
            "recommendation": "Stop automatic retries and require manual review or another payment method."
        }

    elif "opted out" in failure_reason:
        return {
            "failure_category": "Customer Opted Out",
            "recommendation": "Do not retry automatically because the customer has opted out."
        }

    elif failure_reason:
        return {
            "failure_category": "Other Failure",
            "recommendation": "Ask the customer to retry the payment or use another payment method."
        }

    else:
        return {
            "failure_category": "Unknown",
            "recommendation": "Unable to determine the failure reason."
        }
