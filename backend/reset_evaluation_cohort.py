
import random

from backend.database import SessionLocal
from backend.models import (
    Customer,
    Payment,
    PaymentAttempt,
    RecoveryCase,
    RecoveryAction,
)


# =========================================================
# CONFIGURATION
# =========================================================

TOTAL_PAYMENTS = 500
ORDER_PREFIX = "RECOVERAI-ORD-"
CUSTOMER_PREFIX = "evaluation_customer"

# Same fixed seed as seed_data.py.
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

    print("=" * 60)
    print("RecoverAI — Safe Evaluation Cohort Reset")
    print("=" * 60)

    # =====================================================
    # 1. FIND ONLY THE BENCHMARK PAYMENTS
    # =====================================================

    benchmark_payments = (
        db.query(Payment)
        .filter(
            Payment.order_id.like(f"{ORDER_PREFIX}%")
        )
        .all()
    )

    print()
    print(
        f"Existing benchmark payments found: "
        f"{len(benchmark_payments)}"
    )

    # =====================================================
    # 2. DELETE ONLY BENCHMARK PAYMENT DATA
    # =====================================================

    if benchmark_payments:

        benchmark_payment_ids = [
            payment.id
            for payment in benchmark_payments
        ]

        benchmark_cases = (
            db.query(RecoveryCase)
            .filter(
                RecoveryCase.payment_id.in_(
                    benchmark_payment_ids
                )
            )
            .all()
        )

        benchmark_case_ids = [
            case.id
            for case in benchmark_cases
        ]

        print(
            f"Benchmark recovery cases found: "
            f"{len(benchmark_cases)}"
        )

        # -------------------------------------------------
        # RecoveryAction → RecoveryCase
        # -------------------------------------------------

        if benchmark_case_ids:

            deleted_actions = (
                db.query(RecoveryAction)
                .filter(
                    RecoveryAction.recovery_case_id.in_(
                        benchmark_case_ids
                    )
                )
                .delete(
                    synchronize_session=False
                )
            )

            print(
                f"Deleted benchmark recovery actions: "
                f"{deleted_actions}"
            )

        # -------------------------------------------------
        # RecoveryCase → Payment
        # -------------------------------------------------

        deleted_cases = (
            db.query(RecoveryCase)
            .filter(
                RecoveryCase.payment_id.in_(
                    benchmark_payment_ids
                )
            )
            .delete(
                synchronize_session=False
            )
        )

        print(
            f"Deleted benchmark recovery cases: "
            f"{deleted_cases}"
        )

        # -------------------------------------------------
        # PaymentAttempt → Payment
        # -------------------------------------------------

        deleted_attempts = (
            db.query(PaymentAttempt)
            .filter(
                PaymentAttempt.payment_id.in_(
                    benchmark_payment_ids
                )
            )
            .delete(
                synchronize_session=False
            )
        )

        print(
            f"Deleted benchmark payment attempts: "
            f"{deleted_attempts}"
        )

        # -------------------------------------------------
        # Payment
        # -------------------------------------------------

        deleted_payments = (
            db.query(Payment)
            .filter(
                Payment.id.in_(benchmark_payment_ids)
            )
            .delete(
                synchronize_session=False
            )
        )

        print(
            f"Deleted benchmark payments: "
            f"{deleted_payments}"
        )

        db.commit()

        print()
        print("Old benchmark payment data removed safely.")

    else:

        print()
        print("No existing benchmark payment cohort found.")

    # =====================================================
    # 3. REUSE OR CREATE 500 BENCHMARK CUSTOMERS
    # =====================================================

    customers = []
    created_customers = 0
    reused_customers = 0

    for i in range(1, TOTAL_PAYMENTS + 1):

        email = (
            f"{CUSTOMER_PREFIX}{i}"
            "@recoverai.test"
        )

        existing_customer = (
            db.query(Customer)
            .filter(
                Customer.email == email
            )
            .first()
        )

        if existing_customer:

            customers.append(existing_customer)
            reused_customers += 1

        else:

            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            customer = Customer(
                name=f"{first_name} {last_name}",
                email=email
            )

            db.add(customer)
            db.flush()

            customers.append(customer)
            created_customers += 1

    db.commit()

    print()
    print(
        f"Benchmark customers created: "
        f"{created_customers}"
    )

    print(
        f"Benchmark customers reused: "
        f"{reused_customers}"
    )

    print(
        f"Benchmark customers available: "
        f"{len(customers)}"
    )

    # =====================================================
    # 4. CREATE 500 BENCHMARK PAYMENTS
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
            order_id=f"{ORDER_PREFIX}{i:04d}",
            failure_reason=failure_reason
        )

        payments.append(payment)

    db.add_all(payments)
    db.commit()

    for payment in payments:
        db.refresh(payment)

    print(
        f"Created benchmark payments: "
        f"{len(payments)}"
    )

    # =====================================================
    # 5. CREATE INITIAL PAYMENT ATTEMPTS
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

    print(
        f"Created benchmark payment attempts: "
        f"{len(attempts)}"
    )

    # =====================================================
    # 6. CREATE RECOVERY CASES
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

    print(
        f"Created benchmark recovery cases: "
        f"{len(recovery_cases)}"
    )

    # =====================================================
    # 7. CREATE INITIAL RECOVERY ACTIONS
    # =====================================================

    actions = []

    payment_by_id = {
        payment.id: payment
        for payment in payments
    }

    for case in recovery_cases:

        payment = payment_by_id[case.payment_id]

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
    # 8. DATASET SUMMARY
    # =====================================================

    print()
    print("=" * 60)
    print("Clean RecoverAI evaluation dataset created")
    print("=" * 60)

    print(f"Customers:        {len(customers)}")
    print(f"Payments:         {len(payments)}")
    print(f"Attempts:         {len(attempts)}")
    print(f"Recovery cases:   {len(recovery_cases)}")
    print(f"Recovery actions: {len(actions)}")

    print("=" * 60)

    # =====================================================
    # 9. FAILURE DISTRIBUTION
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

    # =====================================================
    # 10. VERIFY EXPERIMENT COHORT
    # =====================================================

    experiment_count = (
        db.query(Payment)
        .filter(
            Payment.order_id.like("RECOVERAI-EXP-%")
        )
        .count()
    )

    print()
    print(
        f"Experiment cohort preserved: "
        f"{experiment_count} payments"
    )

    print("=" * 60)
    print("RESET COMPLETED SUCCESSFULLY")
    print("=" * 60)


except Exception as e:

    db.rollback()

    print()
    print("=" * 60)
    print("ERROR — evaluation cohort reset failed")
    print("=" * 60)
    print(e)

    raise

finally:

    db.close()

