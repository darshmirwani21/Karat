"""
Database models for Karat financial data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum


class TransactionCategory(enum.Enum):
    """Transaction categories from Plaid"""
    FOOD_AND_DRINK = "food_and_drink"
    GENERAL_MERCHANDISE = "general_merchandise"
    TRANSPORTATION = "transportation"
    GAS_STATIONS = "gas_stations"
    GROCERIES = "groceries"
    RESTAURANTS = "restaurants"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    RENT = "rent"
    INCOME = "income"
    TRANSFER = "transfer"
    OTHER = "other"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    accounts = relationship("Account", back_populates="user")
    plaid_items = relationship("PlaidItem", back_populates="user")
    goals = relationship("SavingsGoal", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)


class PlaidItem(Base):
    """Plaid item (one bank connection); holds access_token for API calls"""
    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plaid_item_id = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)  # encrypt in production
    transactions_cursor = Column(Text, nullable=True)  # for transactions_sync pagination
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_item")


class Account(Base):
    """Bank account model"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("plaid_items.id"), nullable=True)  # null if not from Plaid
    plaid_account_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String)  # checking, savings, credit, etc.
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_synced = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    """Transaction model"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    plaid_transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    merchant_name = Column(String)
    category = Column(Enum(TransactionCategory), default=TransactionCategory.OTHER)
    description = Column(Text)
    is_pending = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    account = relationship("Account", back_populates="transactions")


class SavingsGoal(Base):
    """Savings goal model"""
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="goals")
    recommendations = relationship("SavingsRecommendation", back_populates="goal")


class SavingsRecommendation(Base):
    """AI-generated savings recommendations"""
    __tablename__ = "savings_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("savings_goals.id"), nullable=False)
    week_start = Column(DateTime(timezone=True), nullable=False)
    recommended_amount = Column(Float, nullable=False)
    reasoning = Column(Text)
    user_approved = Column(Boolean, default=None)  # None = pending, True/False = user decision
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    goal = relationship("SavingsGoal", back_populates="recommendations")


class UserPreference(Base):
    """User preferences for AI recommendations"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    risk_tolerance = Column(String, default="moderate")  # conservative, moderate, aggressive
    preferred_savings_frequency = Column(String, default="weekly")  # daily, weekly, monthly
    min_emergency_fund = Column(Float, default=1000.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

