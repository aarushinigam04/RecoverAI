import random

from backend.database import SessionLocal
from backend.models import (
    Customer,
    Payment,
    PaymentAttempt,
    RecoveryCase,
    RecoveryAction
)


# =========================================================
# CONFIGURATION
# =========================================================

TOTAL_PAYMENTS = 500

# Fixed seed makes the evaluation dataset reproducible.
random.seed(42)


# =========================================================
# SYNTHETIC DATA
# =========================================================

FIRST_NAMES = [
    "Rahul", "Priya", "Aman", "Sneha", "Arjun",
    "Ananya", "Rohan", "Neha", "Karan", "Pooja",
    "Aditya", "Isha", "Vikram", "Meera", "Nikhil",
    "Kavya", "Sahil", "Riya", "Varun", "Simran"
]

LAST_NAMES = [
    "Sharma", "Singh", "Verma", "Gupta", "Kumar",
    "Mishra", "Agarwal", "Tiwari", "Srivastava",
    "Malhotra"
]


# These are intentionally varied so the recovery engine
# gets multiple types of payment failures.
FAILURE_TYPES = [
    ("bank timeout", 15),
    ("network timeout", 12),
    ("network connectivity issue", 8),
    ("insufficient funds", 12),
    ("card expired", 8),
    ("payment declined", 10),
    ("invalid payment details", 7),
    ("fraud detected", 5),
    ("duplicate webhook", 4),
    ("LLM timeout", 4),
    ("Payment API unavailable", 4),
    ("Payment already captured", 3),
    ("Retry limit exceeded", 3),
    ("Customer opted out", 3),
    ("High-value payment requiring approval", 2),
]


def choose_failure_reason():
    reasons = [item[0] for item in FAILURE_TYPES]
    weights = [item[1] for item in FAILURE_TYPES]

    return random.choices(
        reasons,
        weights=weights,
        k=1
    )[0]


def choose_amount(failure_reason):

    # Guarantee that high-value cases really are high-value.
    if failure_reason == "High-value payment requiring approval":
        return round(random.uniform(50001, 100000), 2)

    return round(
        random.uniform(299, 10000),
        2
    )


# =========================================================
# DATABASE
# =========================================================

db = SessionLocal()


try:

    # =====================================================
    # 1. REMOVE OLD TEST DATA
    # =====================================================

    print("Removing old test data...")

    # Delete child records first because of foreign keys.
    db.query(RecoveryAction).delete()
    db.query(RecoveryCase).delete()
    db.query(PaymentAttempt).delete()
    db.query(Payment).delete()
    db.query(Customer).delete()

    db.commit()

    print("Old test data removed.")

    # =====================================================
    # 2. CREATE CUSTOMERS
    # =====================================================

    customers = []

    for i in range(1, TOTAL_PAYMENTS + 1):

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        customer = Customer(
            name=f"{first_name} {last_name}",
            email=f"customer{i}@recoverai.test"
        )

        customers.append(customer)

    db.add_all(customers)
    db.commit()

    for customer in customers:
        db.refresh(customer)

    print(f"Created customers: {len(customers)}")

    # =====================================================
    # 3. CREATE PAYMENTS
    # =====================================================

    payments = []

    for i in range(1, TOTAL_PAYMENTS + 1):

        failure_reason = choose_failure_reason()

        amount = choose_amount(
            failure_reason
        )

        payment = Payment(
            customer_id=random.choice(customers).id,
            amount=amount,
            currency="INR",
            status="failed",
            order_id=f"RECOVERAI-ORD-{i:04d}",
            failure_reason=failure_reason
        )

        payments.append(payment)

    db.add_all(payments)
    db.commit()

    for payment in payments:
        db.refresh(payment)

    print(f"Created payments: {len(payments)}")

    # =====================================================
    # 4. CREATE INITIAL PAYMENT ATTEMPTS
    # =====================================================

    attempts = []

    for payment in payments:

        attempt = PaymentAttempt(
            payment_id=payment.id,
            status="failed",
            failure_reason=payment.failure_reason
        )

        attempts.append(attempt)

    db.add_all(attempts)
    db.commit()

    print(f"Created payment attempts: {len(attempts)}")

    # =====================================================
    # 5. CREATE RECOVERY CASES
    # =====================================================

    recovery_cases = []

    for payment in payments:

        if payment.amount > 50000:
            priority = "high"

        elif payment.amount > 10000:
            priority = "medium"

        else:
            priority = "low"

        case = RecoveryCase(
            payment_id=payment.id,
            status="open",
            priority=priority
        )

        recovery_cases.append(case)

    db.add_all(recovery_cases)
    db.commit()

    for case in recovery_cases:
        db.refresh(case)

    print(f"Created recovery cases: {len(recovery_cases)}")

    # =====================================================
    # 6. CREATE INITIAL RECOVERY ACTIONS
    # =====================================================

    actions = []

    for case in recovery_cases:

        payment = next(
            p for p in payments
            if p.id == case.payment_id
        )

        reason = payment.failure_reason.lower()

        # -------------------------------------------------
        # TEMPORARY FAILURES
        # -------------------------------------------------

        if (
            "timeout" in reason
            or "network" in reason
            or "api unavailable" in reason
        ):

            action_type = "retry_payment"

            message = (
                "Temporary payment failure detected. "
                "Payment can be retried."
            )

        # -------------------------------------------------
        # INSUFFICIENT FUNDS
        # -------------------------------------------------

        elif "insufficient" in reason:

            action_type = "retry_after_funds_added"

            message = (
                "Customer should add funds before "
                "retrying the payment."
            )

        # -------------------------------------------------
        # EXPIRED CARD / INVALID DETAILS
        # -------------------------------------------------

        elif (
            "expired" in reason
            or "invalid payment details" in reason
        ):

            action_type = (
                "ask_customer_to_update_payment_method"
            )

            message = (
                "Customer should update payment details "
                "before retrying."
            )

        # -------------------------------------------------
        # BANK DECLINED
        # -------------------------------------------------

        elif "declined" in reason:

            action_type = "ask_customer_to_contact_bank"

            message = (
                "Customer should contact their bank "
                "or use another payment method."
            )

        # -------------------------------------------------
        # HIGH VALUE
        # -------------------------------------------------

        elif "high-value" in reason:

            action_type = "require_human_review"

            message = (
                "High-value payment requires human "
                "approval before recovery."
            )

        # -------------------------------------------------
        # BLOCKED CASES
        # -------------------------------------------------

        elif (
            "fraud" in reason
            or "opted out" in reason
            or "retry limit" in reason
        ):

            action_type = "do_not_retry"

            message = (
                "Automatic recovery should not be "
                "performed for this payment."
            )

        # -------------------------------------------------
        # ALREADY CAPTURED
        # -------------------------------------------------

        elif "already captured" in reason:

            action_type = "do_not_retry"

            message = (
                "Payment is already captured. "
                "No retry is required."
            )

        # -------------------------------------------------
        # DUPLICATE WEBHOOK
        # -------------------------------------------------

        elif "duplicate webhook" in reason:

            action_type = "do_not_retry"

            message = (
                "Duplicate webhook detected. "
                "Original payment record should be retained."
            )

        # -------------------------------------------------
        # LLM TIMEOUT
        # -------------------------------------------------

        elif "llm timeout" in reason:

            action_type = "retry_payment"

            message = (
                "AI diagnosis timed out. "
                "Fallback recovery process can retry diagnosis."
            )

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        else:

            action_type = "retry_payment"

            message = (
                "Payment can be evaluated for recovery."
            )

        action = RecoveryAction(
            recovery_case_id=case.id,
            action_type=action_type,
            message=message,
            status="pending"
        )

        actions.append(action)

    db.add_all(actions)
    db.commit()

    # =====================================================
    # 7. DATASET SUMMARY
    # =====================================================

    print()
    print("=" * 60)
    print("RecoverAI synthetic evaluation dataset created")
    print("=" * 60)

    print(f"Customers:        {len(customers)}")
    print(f"Payments:         {len(payments)}")
    print(f"Attempts:         {len(attempts)}")
    print(f"Recovery cases:   {len(recovery_cases)}")
    print(f"Recovery actions: {len(actions)}")

    print("=" * 60)

    # =====================================================
    # 8. FAILURE DISTRIBUTION
    # =====================================================

    print()
    print("Failure distribution:")

    distribution = {}

    for payment in payments:

        reason = payment.failure_reason

        distribution[reason] = (
            distribution.get(reason, 0) + 1
        )

    for reason, count in sorted(
        distribution.items(),
        key=lambda item: item[1],
        reverse=True
    ):

        print(
            f"{reason:<45} {count}"
        )

    print("=" * 60)


except Exception as e:

    db.rollback()

    print()
    print("ERROR while creating synthetic dataset:")
    print(e)


finally:

    db.close()