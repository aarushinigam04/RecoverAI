from backend.database import SessionLocal
from backend.models import (
    Customer,
    Payment,
    PaymentAttempt,
    RecoveryCase,
    RecoveryAction
)


db = SessionLocal()

try:
    # -------------------------
    # 1. Create customers
    # -------------------------

    customer1 = Customer(
        name="Rahul Sharma",
        email="rahul@example.com"
    )

    customer2 = Customer(
        name="Priya Singh",
        email="priya@example.com"
    )

    customer3 = Customer(
        name="Aman Verma",
        email="aman@example.com"
    )

    customer4 = Customer(
        name="Sneha Gupta",
        email="sneha@example.com"
    )

    db.add_all([
        customer1,
        customer2,
        customer3,
        customer4
    ])

    db.commit()

    # -------------------------
    # 2. Create payments
    # -------------------------

    payment1 = Payment(
        customer_id=customer1.id,
        amount=2499.00,
        currency="INR",
        status="failed",
        order_id="ORD-1001"
    )

    payment2 = Payment(
        customer_id=customer2.id,
        amount=1499.00,
        currency="INR",
        status="failed",
        order_id="ORD-1002"
    )

    payment3 = Payment(
        customer_id=customer3.id,
        amount=3999.00,
        currency="INR",
        status="success",
        order_id="ORD-1003"
    )

    payment4 = Payment(
        customer_id=customer4.id,
        amount=799.00,
        currency="INR",
        status="failed",
        order_id="ORD-1004"
    )

    db.add_all([
        payment1,
        payment2,
        payment3,
        payment4
    ])

    db.commit()

    # -------------------------
    # 3. Create payment attempts
    # -------------------------

    attempt1 = PaymentAttempt(
        payment_id=payment1.id,
        status="failed",
        failure_reason="insufficient_funds"
    )

    attempt2 = PaymentAttempt(
        payment_id=payment2.id,
        status="failed",
        failure_reason="bank_declined"
    )

    attempt3 = PaymentAttempt(
        payment_id=payment3.id,
        status="success",
        failure_reason=None
    )

    attempt4 = PaymentAttempt(
        payment_id=payment4.id,
        status="failed",
        failure_reason="network_error"
    )

    db.add_all([
        attempt1,
        attempt2,
        attempt3,
        attempt4
    ])

    db.commit()

    # -------------------------
    # 4. Create recovery cases
    # -------------------------

    case1 = RecoveryCase(
        payment_id=payment1.id,
        status="open",
        priority="high"
    )

    case2 = RecoveryCase(
        payment_id=payment2.id,
        status="open",
        priority="medium"
    )

    case3 = RecoveryCase(
        payment_id=payment4.id,
        status="open",
        priority="low"
    )

    db.add_all([
        case1,
        case2,
        case3
    ])

    db.commit()

    # -------------------------
    # 5. Create recovery actions
    # -------------------------

    action1 = RecoveryAction(
        recovery_case_id=case1.id,
        action_type="retry_payment",
        message="Customer may retry payment using another payment method.",
        status="pending"
    )

    action2 = RecoveryAction(
        recovery_case_id=case2.id,
        action_type="send_reminder",
        message="Send payment reminder to customer.",
        status="pending"
    )

    action3 = RecoveryAction(
        recovery_case_id=case3.id,
        action_type="retry_payment",
        message="Temporary network issue detected. Suggest retry.",
        status="pending"
    )

    db.add_all([
        action1,
        action2,
        action3
    ])

    db.commit()

    print("✅ Test data added successfully!")

except Exception as e:
    db.rollback()
    print("❌ Error:", e)

finally:
    db.close()