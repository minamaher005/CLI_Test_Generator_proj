class BankAccount:
    """A tiny bank account with a transaction history."""

    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self.balance = balance
        self.history: list[str] = []

    def deposit(self, amount: float) -> float:
        """Add money; the new balance is returned. Zero/negative is rejected."""
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.balance += amount
        self.history.append(f"deposit {amount}")
        return self.balance

    def withdraw(self, amount: float) -> float:
        """Remove money; the new balance is returned. Negative amounts and
        overdrafts are rejected."""
        if amount <= 0:
            raise ValueError("Withdrawal must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.history.append(f"withdraw {amount}")
        return self.balance


def transfer(src: "BankAccount", dst: "BankAccount", amount: float) -> None:
    """Move amount from one account to another (withdraw, then deposit)."""
    src.withdraw(amount)
    dst.deposit(amount)
