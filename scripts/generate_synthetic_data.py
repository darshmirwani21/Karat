#!/usr/bin/env python3
"""
Synthetic data generator for Karat AI Financial Assistant
Creates realistic demo data for development and testing
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
import random

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from faker import Faker
from sqlalchemy.orm import Session
from database.connection import engine, SessionLocal
from database.models import User, Account, Transaction, SavingsGoal, TransactionCategory
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

fake = Faker()

def create_demo_user(db: Session) -> User:
    """Create demo user if it doesn't exist"""
    existing_user = db.query(User).filter(User.id == 1).first()
    if existing_user:
        print("Demo user already exists (id=1)")
        return existing_user
    
    user = User(
        id=1,
        email="demo@karat.app",
        full_name="Demo User",
        hashed_password="demo_hash"  # Simple hash for demo
    )
    db.add(user)
    db.commit()
    print("Created demo user (id=1)")
    return user

def create_demo_accounts(db: Session, user: User) -> List[Account]:
    """Create checking and savings accounts for demo user"""
    accounts = []
    
    # Checking account
    checking = Account(
        user_id=user.id,
        plaid_account_id=str(uuid.uuid4()),
        name="Demo Checking Account",
        type="checking",
        balance=2500.00
    )
    accounts.append(checking)
    
    # Savings account
    savings = Account(
        user_id=user.id,
        plaid_account_id=str(uuid.uuid4()),
        name="Demo Savings Account",
        type="savings",
        balance=8500.00
    )
    accounts.append(savings)
    
    db.add_all(accounts)
    db.commit()
    print(f"Created {len(accounts)} accounts for demo user")
    return accounts

def generate_transactions(db: Session, accounts: List[Account]) -> List[Transaction]:
    """Generate 12 months of realistic transactions"""
    transactions = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    current_date = start_date
    while current_date <= end_date:
        # Skip some days for realism
        if random.random() < 0.15:  # 15% chance of no transactions
            current_date += timedelta(days=1)
            continue
        
        # Generate 1-4 transactions per day
        num_transactions = random.randint(1, 4)
        
        for _ in range(num_transactions):
            account = random.choice(accounts)
            transaction = generate_single_transaction(current_date, account)
            if transaction:
                transactions.append(transaction)
        
        current_date += timedelta(days=1)
    
    db.add_all(transactions)
    db.commit()
    print(f"Generated {len(transactions)} transactions over 12 months")
    return transactions

def generate_single_transaction(date: datetime, account: Account) -> Transaction:
    """Generate a single realistic transaction"""
    
    # Seasonal variance for Nov/Dec
    is_holiday_season = date.month in [11, 12]
    holiday_multiplier = 1.3 if is_holiday_season else 1.0
    
    # Transaction types with their probabilities
    transaction_types = [
        ("income", 0.08, generate_income_transaction),
        ("groceries", 0.15, lambda d, a: generate_expense_transaction(d, a, "groceries", 40, 180)),
        ("restaurants", 0.20, lambda d, a: generate_expense_transaction(d, a, "restaurants", 12, 65, holiday_multiplier)),
        ("gas_stations", 0.08, lambda d, a: generate_expense_transaction(d, a, "gas_stations", 35, 80)),
        ("utilities", 0.03, lambda d, a: generate_utility_transaction(d, a)),
        ("entertainment", 0.12, lambda d, a: generate_expense_transaction(d, a, "entertainment", 10, 120, holiday_multiplier)),
        ("transportation", 0.10, lambda d, a: generate_expense_transaction(d, a, "transportation", 15, 60)),
        ("rent", 0.02, lambda d, a: generate_rent_transaction(d, a)),
        ("general_merchandise", 0.22, lambda d, a: generate_expense_transaction(d, a, "general_merchandise", 20, 150, holiday_multiplier)),
    ]
    
    # Choose transaction type based on probability
    rand_val = random.random()
    cumulative_prob = 0
    
    for trans_type, prob, generator in transaction_types:
        cumulative_prob += prob
        if rand_val <= cumulative_prob:
            return generator(date, account)
    
    return None

def generate_income_transaction(date: datetime, account: Account) -> Transaction:
    """Generate income transaction (negative amount)"""
    # Twice per month on 1st and 15th
    if date.day not in [1, 15]:
        return None
    
    amount = -random.uniform(2800, 3800)  # Negative for income
    
    return Transaction(
        account_id=account.id,
        plaid_transaction_id=str(uuid.uuid4()),
        amount=amount,
        date=date,
        merchant_name="Direct Deposit",
        category=TransactionCategory.INCOME,
        description="Monthly salary"
    )

def generate_expense_transaction(date: datetime, account: Account, category_str: str, 
                                min_amount: float, max_amount: float, multiplier: float = 1.0) -> Transaction:
    """Generate expense transaction"""
    category_map = {
        "groceries": TransactionCategory.GROCERIES,
        "restaurants": TransactionCategory.RESTAURANTS,
        "gas_stations": TransactionCategory.GAS_STATIONS,
        "entertainment": TransactionCategory.ENTERTAINMENT,
        "transportation": TransactionCategory.TRANSPORTATION,
        "general_merchandise": TransactionCategory.GENERAL_MERCHANDISE,
    }
    
    amount = random.uniform(min_amount, max_amount) * multiplier
    merchant = generate_merchant_name(category_str)
    
    return Transaction(
        account_id=account.id,
        plaid_transaction_id=str(uuid.uuid4()),
        amount=amount,
        date=date,
        merchant_name=merchant,
        category=category_map[category_str],
        description=f"{merchant} purchase"
    )

def generate_utility_transaction(date: datetime, account: Account) -> Transaction:
    """Generate monthly utility transaction"""
    if date.day != 5:  # Utilities on 5th of month
        return None
    
    amount = random.uniform(80, 200)
    utility_types = ["Electric Bill", "Water Bill", "Internet", "Gas Bill", "Phone Bill"]
    merchant = random.choice(utility_types)
    
    return Transaction(
        account_id=account.id,
        plaid_transaction_id=str(uuid.uuid4()),
        amount=amount,
        date=date,
        merchant_name=merchant,
        category=TransactionCategory.UTILITIES,
        description=f"Monthly {merchant.lower()}"
    )

def generate_rent_transaction(date: datetime, account: Account) -> Transaction:
    """Generate monthly rent transaction"""
    if date.day != 1:  # Rent on 1st of month
        return None
    
    amount = random.uniform(1100, 1400)
    
    return Transaction(
        account_id=account.id,
        plaid_transaction_id=str(uuid.uuid4()),
        amount=amount,
        date=date,
        merchant_name="Landlord Property Management",
        category=TransactionCategory.RENT,
        description="Monthly rent payment"
    )

def generate_merchant_name(category: str) -> str:
    """Generate realistic merchant names by category"""
    merchants = {
        "groceries": ["Walmart", "Kroger", "Whole Foods", "Trader Joe's", "Safeway", "Publix"],
        "restaurants": ["McDonald's", "Starbucks", "Chipotle", "Panera Bread", "Subway", "Local Cafe"],
        "gas_stations": ["Shell", "Chevron", "BP", "Exxon", "Mobil", "Sunoco"],
        "entertainment": ["Netflix", "Spotify", "AMC Theaters", "Steam", "PlayStation Store", "Xbox"],
        "transportation": ["Uber", "Lyft", "Taxi", "Public Transit", "Parking Garage"],
        "general_merchandise": ["Amazon", "Target", "Best Buy", "Home Depot", "Costco", "Walgreens"]
    }
    
    return random.choice(merchants.get(category, ["Generic Store"]))

def create_savings_goals(db: Session, user: User) -> List[SavingsGoal]:
    """Create demo savings goals"""
    goals = []
    
    # Holiday Fund
    holiday_date = datetime(datetime.now().year, 12, 15)
    if holiday_date < datetime.now():
        holiday_date = datetime(datetime.now().year + 1, 12, 15)
    
    holiday_goal = SavingsGoal(
        user_id=user.id,
        name="Holiday Fund",
        target_amount=600.0,
        current_amount=120.0,
        target_date=holiday_date
    )
    goals.append(holiday_goal)
    
    # Emergency Fund
    emergency_date = datetime.now() + timedelta(days=180)  # 6 months from now
    
    emergency_goal = SavingsGoal(
        user_id=user.id,
        name="Emergency Fund",
        target_amount=2000.0,
        current_amount=450.0,
        target_date=emergency_date
    )
    goals.append(emergency_goal)
    
    db.add_all(goals)
    db.commit()
    print(f"Created {len(goals)} savings goals")
    return goals

def main():
    """Main function to generate all synthetic data"""
    print("Starting synthetic data generation...")
    
    # Check database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in backend/.env file")
        return
    
    print(f"Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create demo user
        user = create_demo_user(db)
        
        # Create accounts
        accounts = create_demo_accounts(db, user)
        
        # Generate transactions
        transactions = generate_transactions(db, accounts)
        
        # Create savings goals
        goals = create_savings_goals(db, user)
        
        # Print summary
        print("\n" + "="*50)
        print("SYNTHETIC DATA GENERATION COMPLETE")
        print("="*50)
        print(f"✓ User: {user.full_name} ({user.email})")
        print(f"✓ Accounts: {len(accounts)}")
        print(f"✓ Transactions: {len(transactions)}")
        print(f"✓ Savings Goals: {len(goals)}")
        print("="*50)
        
    except Exception as e:
        print(f"Error during data generation: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
