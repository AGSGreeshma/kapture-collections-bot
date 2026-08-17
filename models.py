from sqlalchemy import Column, String, Integer
from database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    loan_type = Column(String, nullable=False)
    overdue_amount = Column(Integer, nullable=False)
    days_past_due = Column(Integer, nullable=False)
    payment_status = Column(String, nullable=False)
    verification_code = Column(String, nullable=False)


class PaymentPromise(Base):
    __tablename__ = "payment_promises"

    promise_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    promised_date = Column(String, nullable=False)
    status = Column(String, nullable=False)