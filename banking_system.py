import json
import uuid
import hashlib
import getpass
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class Account(ABC):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0, password: str = ""):
        self._account_number = account_number
        self._account_holder_id = account_holder_id
        self._balance = initial_balance
        self._password_hash = self._hash_password(password) if password else ""
        self._failed_attempts = 0
        self._is_locked = False

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Verify if provided password matches stored hash"""
        if self._is_locked:
            return False
        
        if self._password_hash == self._hash_password(password):
            self._failed_attempts = 0
            return True
        else:
            self._failed_attempts += 1
            if self._failed_attempts >= 3:
                self._is_locked = True
            return False

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def account_holder_id(self) -> str:
        return self._account_holder_id

    @abstractmethod
    def deposit(self, amount: float) -> bool:
        pass

    @abstractmethod
    def withdraw(self, amount: float) -> bool:
        pass

    def display_details(self) -> str:
        return f"Acc No: {self._account_number}, Balance: ₹{self._balance:.2f}"

    def to_dict(self) -> dict:
        return {
            "account_number": self._account_number,
            "account_holder_id": self._account_holder_id,
            "balance": self._balance,
            "password_hash": self._password_hash,
            "failed_attempts": self._failed_attempts,
            "is_locked": self._is_locked
        }

class SavingsAccount(Account):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0, 
                 password: str = "", interest_rate: float = 0.01):
        super().__init__(account_number, account_holder_id, initial_balance, password)
        self._interest_rate = interest_rate

    @property
    def interest_rate(self) -> float:
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value: float):
        if value >= 0:
            self._interest_rate = value

    def deposit(self, amount: float) -> bool:
        if amount > 0:
            self._balance += amount
            return True
        return False

    def withdraw(self, amount: float) -> bool:
        if amount > 0 and self._balance >= amount:
            self._balance -= amount
            return True
        return False

    def apply_interest(self) -> None:
        self._balance += self._balance * self._interest_rate

    def display_details(self) -> str:
        base = super().display_details()
        return f"{base}, Type: Savings, Interest Rate: {self._interest_rate:.2%}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "type": "savings",
            "interest_rate": self._interest_rate
        })
        return data

class CheckingAccount(Account):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0, 
                 password: str = "", overdraft_limit: float = 0.0):
        super().__init__(account_number, account_holder_id, initial_balance, password)
        self._overdraft_limit = overdraft_limit

    @property
    def overdraft_limit(self) -> float:
        return self._overdraft_limit

    @overdraft_limit.setter
    def overdraft_limit(self, value: float):
        if value >= 0:
            self._overdraft_limit = value

    def deposit(self, amount: float) -> bool:
        if amount > 0:
            self._balance += amount
            return True
        return False

    def withdraw(self, amount: float) -> bool:
        if amount > 0 and (self._balance - amount) >= -self._overdraft_limit:
            self._balance -= amount
            return True
        return False

    def display_details(self) -> str:
        base = super().display_details()
        return f"{base}, Type: Checking, Overdraft Limit: ₹{self._overdraft_limit:.2f}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "type": "checking",
            "overdraft_limit": self._overdraft_limit
        })
        return data

class Customer:
    def __init__(self, customer_id: str, name: str, address: str):
        self._customer_id = customer_id
        self._name = name
        self._address = address
        self._account_numbers: List[str] = []

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str):
        self._address = value

    @property
    def account_numbers(self) -> List[str]:
        return self._account_numbers.copy()

    def add_account_number(self, account_number: str) -> None:
        if account_number not in self._account_numbers:
            self._account_numbers.append(account_number)

    def remove_account_number(self, account_number: str) -> None:
        if account_number in self._account_numbers:
            self._account_numbers.remove(account_number)

    def display_details(self) -> str:
        return (f"Customer ID: {self._customer_id}, Name: {self._name}, "
                f"Address: {self._address}, Accounts: {len(self._account_numbers)}")

    def to_dict(self) -> dict:
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "address": self._address,
            "account_numbers": self._account_numbers
        }

class Bank:
    def __init__(self, customer_file: str = 'customers.json', account_file: str = 'accounts.json'):
        self._customers: Dict[str, Customer] = {}
        self._accounts: Dict[str, Account] = {}
        self._customer_file = customer_file
        self._account_file = account_file
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self._customer_file, 'r') as f:
                customers_data = json.load(f)
                for customer_data in customers_data.values():
                    customer = Customer(
                        customer_data['customer_id'],
                        customer_data['name'],
                        customer_data['address']
                    )
                    for acc_num in customer_data['account_numbers']:
                        customer.add_account_number(acc_num)
                    self._customers[customer.customer_id] = customer
        except FileNotFoundError:
            pass

        try:
            with open(self._account_file, 'r') as f:
                accounts_data = json.load(f)
                for acc_data in accounts_data.values():
                    if acc_data['type'] == 'savings':
                        account = SavingsAccount(
                            acc_data['account_number'],
                            acc_data['account_holder_id'],
                            acc_data['balance'],
                            "",
                            acc_data['interest_rate']
                        )
                    elif acc_data['type'] == 'checking':
                        account = CheckingAccount(
                            acc_data['account_number'],
                            acc_data['account_holder_id'],
                            acc_data['balance'],
                            "",
                            acc_data['overdraft_limit']
                        )
                    else:
                        continue
                    
                    # Restore password and security fields
                    account._password_hash = acc_data.get('password_hash', '')
                    account._failed_attempts = acc_data.get('failed_attempts', 0)
                    account._is_locked = acc_data.get('is_locked', False)
                    
                    self._accounts[account.account_number] = account
        except FileNotFoundError:
            pass

    def _save_data(self) -> None:
        customers_data = {cid: cust.to_dict() for cid, cust in self._customers.items()}
        accounts_data = {anum: acc.to_dict() for anum, acc in self._accounts.items()}

        with open(self._customer_file, 'w') as f:
            json.dump(customers_data, f, indent=2)

        with open(self._account_file, 'w') as f:
            json.dump(accounts_data, f, indent=2)

    def add_customer(self, customer: Customer) -> bool:
        if customer.customer_id in self._customers:
            return False
        self._customers[customer.customer_id] = customer
        self._save_data()
        return True

    def remove_customer(self, customer_id: str) -> bool:
        """Remove a customer with intelligent handling of accounts"""
        if customer_id not in self._customers:
            print(f"Error: Customer ID '{customer_id}' not found.")
            return False
        
        customer = self._customers[customer_id]
        
        # Check if customer has accounts
        if customer.account_numbers:
            print(f"Customer '{customer_id}' has {len(customer.account_numbers)} active account(s).")
            
            # Show account details
            print("Account details:")
            for acc_num in customer.account_numbers:
                if acc_num in self._accounts:
                    account = self._accounts[acc_num]
                    print(f"  - {account.display_details()}")
            
            # Ask user what to do
            print("\nOptions:")
            print("1. Cancel removal (keep customer and accounts)")
            print("2. Remove customer and close all accounts (balances will be lost)")
            
            choice = input("Enter your choice (1-2): ")
            
            if choice == '1':
                print("Customer removal cancelled.")
                return False
            elif choice == '2':
                # Check for non-zero balances
                accounts_with_balance = []
                for acc_num in customer.account_numbers:
                    if acc_num in self._accounts:
                        account = self._accounts[acc_num]
                        if account.balance != 0:
                            accounts_with_balance.append((acc_num, account.balance))
                
                if accounts_with_balance:
                    print("\nWarning: The following accounts have non-zero balances:")
                    for acc_num, balance in accounts_with_balance:
                        print(f"  - Account {acc_num}: ₹{balance:.2f}")
                    
                    confirm = input("Type 'CONFIRM' to proceed with removal (balances will be lost): ")
                    if confirm != 'CONFIRM':
                        print("Customer removal cancelled.")
                        return False
                
                # Remove all accounts
                accounts_to_remove = customer.account_numbers.copy()
                for account_number in accounts_to_remove:
                    if account_number in self._accounts:
                        del self._accounts[account_number]
                
                print(f"Removed {len(accounts_to_remove)} account(s).")
            else:
                print("Invalid choice. Customer removal cancelled.")
                return False
        
        # Remove the customer
        del self._customers[customer_id]
        self._save_data()
        print(f"Customer '{customer_id}' has been removed successfully.")
        return True

    def create_account(self, customer_id: str, account_type: str, initial_balance: float = 0.0, 
                      password: str = "", **kwargs) -> Optional[Account]:
        if customer_id not in self._customers:
            return None

        account_number = str(uuid.uuid4())[:8]
        account = None

        if account_type.lower() == 'savings':
            interest_rate = kwargs.get('interest_rate', 0.01)
            account = SavingsAccount(account_number, customer_id, initial_balance, password, interest_rate)
        elif account_type.lower() == 'checking':
            overdraft_limit = kwargs.get('overdraft_limit', 0.0)
            account = CheckingAccount(account_number, customer_id, initial_balance, password, overdraft_limit)
        else:
            return None

        self._accounts[account_number] = account
        self._customers[customer_id].add_account_number(account_number)
        self._save_data()
        return account

    def deposit(self, account_number: str, amount: float) -> bool:
        if account_number not in self._accounts:
            return False
        success = self._accounts[account_number].deposit(amount)
        if success:
            self._save_data()
        return success

    def withdraw(self, account_number: str, amount: float) -> bool:
        if account_number not in self._accounts:
            print("Error: Account not found.")
            return False
        
        account = self._accounts[account_number]
        
        if account._is_locked:
            print("Error: Account is locked due to multiple failed password attempts.")
            return False
        
        password = getpass.getpass("Enter account password: ")
        
        if not account.verify_password(password):
            remaining_attempts = 3 - account._failed_attempts
            if account._is_locked:
                print("Account locked due to multiple failed attempts.")
            else:
                print(f"Incorrect password. {remaining_attempts} attempts remaining.")
            self._save_data()
            return False
        
        success = account.withdraw(amount)
        if success:
            self._save_data()
        return success

    def transfer_funds(self, from_acc_num: str, to_acc_num: str, amount: float) -> bool:
        if from_acc_num not in self._accounts or to_acc_num not in self._accounts:
            return False
        if amount <= 0:
            return False

        from_acc = self._accounts[from_acc_num]
        
        if from_acc._is_locked:
            print("Error: Source account is locked.")
            return False

        password = getpass.getpass(f"Enter password for source account {from_acc_num}: ")
        
        if not from_acc.verify_password(password):
            remaining_attempts = 3 - from_acc._failed_attempts
            if from_acc._is_locked:
                print("Source account locked due to multiple failed attempts.")
            else:
                print(f"Incorrect password. {remaining_attempts} attempts remaining.")
            self._save_data()
            return False

        to_acc = self._accounts[to_acc_num]

        if from_acc.withdraw(amount):
            if to_acc.deposit(amount):
                self._save_data()
                return True
            else:
                from_acc.deposit(amount)
                return False
        return False

    def get_customer_accounts(self, customer_id: str) -> List[Account]:
        if customer_id not in self._customers:
            return []
        return [self._accounts[acc_num] for acc_num in self._customers[customer_id].account_numbers
                if acc_num in self._accounts]

    def display_all_customers(self) -> None:
        if not self._customers:
            print("No customers found.")
            return
        for customer in self._customers.values():
            print(customer.display_details())

    def display_all_accounts(self) -> None:
        if not self._accounts:
            print("No accounts found.")
            return
        for account in self._accounts.values():
            print(account.display_details())

    def apply_all_interest(self) -> None:
        for account in self._accounts.values():
            if isinstance(account, SavingsAccount):
                account.apply_interest()
        self._save_data()

def main():
    bank = Bank()

    while True:
        print("\nBanking System Menu:")
        print("1. Add Customer")
        print("2. Remove Customer")
        print("3. Create Account")
        print("4. Deposit")
        print("5. Withdraw")
        print("6. Transfer Funds")
        print("7. View Customer Accounts")
        print("8. Apply Interest to Savings Accounts")
        print("9. Display All Customers")
        print("10. Display All Accounts")
        print("11. Exit")

        choice = input("Enter your choice (1-11): ")

        if choice == '1':
            customer_id = input("Enter customer ID: ")
            name = input("Enter customer name: ")
            address = input("Enter customer address: ")
            customer = Customer(customer_id, name, address)
            if bank.add_customer(customer):
                print("Customer added successfully.")
            else:
                print("Error: Customer ID already exists.")

        elif choice == '2':
            customer_id = input("Enter customer ID to remove: ")
            bank.remove_customer(customer_id)

        elif choice == '3':
            customer_id = input("Enter customer ID: ")
            
            if customer_id not in bank._customers:
                print(f"Error: Customer ID '{customer_id}' not found. Please add the customer first.")
                continue
                
            account_type = input("Enter account type (savings/checking): ").lower()
            
            try:
                initial_balance = float(input("Enter initial balance: "))
            except ValueError:
                print("Invalid balance amount.")
                continue
            
            password = getpass.getpass("Set a password for the account: ")
            confirm_password = getpass.getpass("Confirm password: ")
            
            if password != confirm_password:
                print("Passwords do not match. Account creation cancelled.")
                continue

            if len(password) < 4:
                print("Password must be at least 4 characters long.")
                continue

            if account_type == 'savings':
                try:
                    interest_rate = float(input("Enter interest rate (e.g., 0.01 for 1%): "))
                    account = bank.create_account(customer_id, account_type, initial_balance, 
                                                password, interest_rate=interest_rate)
                except ValueError:
                    print("Invalid interest rate.")
                    continue
            elif account_type == 'checking':
                try:
                    overdraft_limit = float(input("Enter overdraft limit: "))
                    account = bank.create_account(customer_id, account_type, initial_balance, 
                                                password, overdraft_limit=overdraft_limit)
                except ValueError:
                    print("Invalid overdraft limit.")
                    continue
            else:
                print("Invalid account type.")
                continue

            if account:
                print(f"Account created successfully. Account Number: {account.account_number}")
            else:
                print("Error: Customer not found or invalid account type.")

        elif choice == '4':
            account_number = input("Enter account number: ")
            try:
                amount = float(input("Enter amount to deposit: "))
                if bank.deposit(account_number, amount):
                    print("Deposit successful.")
                else:
                    print("Error: Invalid account number or amount.")
            except ValueError:
                print("Invalid amount.")

        elif choice == '5':
            account_number = input("Enter account number: ")
            try:
                amount = float(input("Enter amount to withdraw: "))
                if bank.withdraw(account_number, amount):
                    print("Withdrawal successful.")
                else:
                    print("Error: Invalid account number, amount, or insufficient funds.")
            except ValueError:
                print("Invalid amount.")

        elif choice == '6':
            from_acc = input("Enter source account number: ")
            to_acc = input("Enter destination account number: ")
            try:
                amount = float(input("Enter amount to transfer: "))
                if bank.transfer_funds(from_acc, to_acc, amount):
                    print("Transfer successful.")
                else:
                    print("Error: Invalid account numbers or insufficient funds.")
            except ValueError:
                print("Invalid amount.")

        elif choice == '7':
            customer_id = input("Enter customer ID: ")
            accounts = bank.get_customer_accounts(customer_id)
            if accounts:
                print(f"\nAccounts for customer {customer_id}:")
                for account in accounts:
                    print(account.display_details())
            else:
                print("No accounts found or customer does not exist.")

        elif choice == '8':
            bank.apply_all_interest()
            print("Interest applied to all savings accounts.")

        elif choice == '9':
            print("\nAll Customers:")
            bank.display_all_customers()

        elif choice == '10':
            print("\nAll Accounts:")
            bank.display_all_accounts()

        elif choice == '11':
            print("Exiting the banking system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 11.")

if __name__ == "__main__":
    main()
