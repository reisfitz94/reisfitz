"""
Financial Transaction System
A Python module for processing financial transactions in a financial institution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from decimal import Decimal
import uuid


class TransactionType(Enum):
    """Types of financial transactions"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"


class TransactionStatus(Enum):
    """Status of a transaction"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Account:
    """Represents a bank account"""
    account_number: str
    account_holder: str
    balance: Decimal
    account_type: str = "Checking"
    currency: str = "USD"
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        if self.balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.balance = Decimal(str(self.balance))
    
    def deposit(self, amount: Decimal) -> bool:
        """Deposit funds to the account"""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        if not self.is_active:
            raise ValueError("Account is not active")
        self.balance += amount
        return True
    
    def withdraw(self, amount: Decimal) -> bool:
        """Withdraw funds from the account"""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if not self.is_active:
            raise ValueError("Account is not active")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return True
    
    def get_balance(self) -> Decimal:
        """Get current account balance"""
        return self.balance


@dataclass
class Transaction:
    """Represents a financial transaction"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    transaction_type: TransactionType = TransactionType.TRANSFER
    from_account: Optional[str] = None
    to_account: Optional[str] = None
    amount: Decimal = Decimal("0")
    status: TransactionStatus = TransactionStatus.PENDING
    description: str = ""
    reference_number: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __post_init__(self):
        self.amount = Decimal(str(self.amount))
    
    def __str__(self) -> str:
        return (f"Transaction(ID: {self.transaction_id}, Type: {self.transaction_type.value}, "
                f"Amount: {self.amount}, Status: {self.status.value})")


class FinancialInstitution:
    """Represents a financial institution like JP Morgan"""
    
    def __init__(self, name: str, routing_number: str):
        self.name = name
        self.routing_number = routing_number
        self.accounts: dict[str, Account] = {}
        self.transactions: List[Transaction] = []
        self.daily_transaction_limit = Decimal("50000")
    
    def create_account(self, account_holder: str, initial_balance: Decimal = Decimal("0"),
                      account_type: str = "Checking") -> Account:
        """Create a new bank account"""
        account_number = f"{self.routing_number}-{len(self.accounts) + 1000}"
        account = Account(
            account_number=account_number,
            account_holder=account_holder,
            balance=initial_balance,
            account_type=account_type
        )
        self.accounts[account_number] = account
        return account
    
    def get_account(self, account_number: str) -> Optional[Account]:
        """Retrieve an account by account number"""
        return self.accounts.get(account_number)
    
    def deposit(self, account_number: str, amount: Decimal, description: str = "Deposit") -> Transaction:
        """Process a deposit transaction"""
        account = self.get_account(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")
        
        transaction = Transaction(
            transaction_type=TransactionType.DEPOSIT,
            to_account=account_number,
            amount=amount,
            description=description
        )
        
        try:
            account.deposit(amount)
            transaction.status = TransactionStatus.COMPLETED
            self.transactions.append(transaction)
            print(f"✓ Deposit successful: ${amount} deposited to {account_number}")
            return transaction
        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            self.transactions.append(transaction)
            raise ValueError(f"Deposit failed: {str(e)}")
    
    def withdraw(self, account_number: str, amount: Decimal, description: str = "Withdrawal") -> Transaction:
        """Process a withdrawal transaction"""
        account = self.get_account(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")
        
        transaction = Transaction(
            transaction_type=TransactionType.WITHDRAWAL,
            from_account=account_number,
            amount=amount,
            description=description
        )
        
        try:
            account.withdraw(amount)
            transaction.status = TransactionStatus.COMPLETED
            self.transactions.append(transaction)
            print(f"✓ Withdrawal successful: ${amount} withdrawn from {account_number}")
            return transaction
        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            self.transactions.append(transaction)
            raise ValueError(f"Withdrawal failed: {str(e)}")
    
    def transfer(self, from_account: str, to_account: str, amount: Decimal,
                description: str = "Transfer") -> Transaction:
        """Process a transfer between two accounts"""
        if from_account not in self.accounts:
            raise ValueError(f"Source account {from_account} not found")
        if to_account not in self.accounts:
            raise ValueError(f"Destination account {to_account} not found")
        
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        # Check daily limit
        daily_total = self._get_daily_transaction_total()
        if daily_total + amount > self.daily_transaction_limit:
            raise ValueError("Daily transaction limit exceeded")
        
        transaction = Transaction(
            transaction_type=TransactionType.TRANSFER,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            description=description
        )
        
        try:
            from_acc = self.accounts[from_account]
            to_acc = self.accounts[to_account]
            
            from_acc.withdraw(amount)
            to_acc.deposit(amount)
            
            transaction.status = TransactionStatus.COMPLETED
            self.transactions.append(transaction)
            print(f"✓ Transfer successful: ${amount} transferred from {from_account} to {to_account}")
            return transaction
        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            self.transactions.append(transaction)
            raise ValueError(f"Transfer failed: {str(e)}")
    
    def _get_daily_transaction_total(self) -> Decimal:
        """Calculate total transaction amount for the current day"""
        today = datetime.now().date()
        daily_total = Decimal("0")
        
        for txn in self.transactions:
            if txn.timestamp.date() == today and txn.status == TransactionStatus.COMPLETED:
                daily_total += txn.amount
        
        return daily_total
    
    def get_transaction_history(self, account_number: str, limit: int = 10) -> List[Transaction]:
        """Get transaction history for an account"""
        history = [t for t in self.transactions 
                  if (t.from_account == account_number or t.to_account == account_number)
                  and t.status == TransactionStatus.COMPLETED]
        return history[-limit:]
    
    def get_account_balance(self, account_number: str) -> Decimal:
        """Get current balance of an account"""
        account = self.get_account(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")
        return account.get_balance()
    
    def print_account_summary(self, account_number: str) -> None:
        """Print a summary of an account"""
        account = self.get_account(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")
        
        print(f"\n{'='*50}")
        print(f"ACCOUNT SUMMARY - {self.name}")
        print(f"{'='*50}")
        print(f"Account Number: {account.account_number}")
        print(f"Account Holder: {account.account_holder}")
        print(f"Account Type: {account.account_type}")
        print(f"Balance: ${account.balance:,.2f} {account.currency}")
        print(f"Status: {'Active' if account.is_active else 'Inactive'}")
        print(f"Created: {account.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")


def main():
    """Main function demonstrating financial transactions"""
    
    # Create financial institution
    jp_morgan = FinancialInstitution("JP Morgan Chase Bank", "021000021")
    
    # Create accounts
    print("Creating accounts...\n")
    alice_account = jp_morgan.create_account("Alice Johnson", Decimal("5000"), "Checking")
    bob_account = jp_morgan.create_account("Bob Smith", Decimal("3000"), "Savings")
    
    print(f"Alice's account: {alice_account.account_number}")
    print(f"Bob's account: {bob_account.account_number}\n")
    
    # Display initial balances
    jp_morgan.print_account_summary(alice_account.account_number)
    jp_morgan.print_account_summary(bob_account.account_number)
    
    # Perform transactions
    print("Processing transactions...\n")
    
    # Deposit
    jp_morgan.deposit(alice_account.account_number, Decimal("1500"), "Salary Deposit")
    
    # Withdrawal
    jp_morgan.withdraw(bob_account.account_number, Decimal("500"), "ATM Withdrawal")
    
    # Transfer
    jp_morgan.transfer(alice_account.account_number, bob_account.account_number, 
                      Decimal("2000"), "Payment for services")
    
    # Display final balances
    print("\n")
    jp_morgan.print_account_summary(alice_account.account_number)
    jp_morgan.print_account_summary(bob_account.account_number)
    
    # Transaction history
    print(f"\nTransaction History for Alice:")
    print(f"{'='*50}")
    for txn in jp_morgan.get_transaction_history(alice_account.account_number):
        print(f"  • {txn.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"{txn.transaction_type.value.upper()} | "
              f"${txn.amount:,.2f} | {txn.status.value} | {txn.description}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
