import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from recon.domain.models import Transaction, BankEntry


class DataLoader:
    @staticmethod
    def load_transactions_csv(filepath: Path) -> List[Transaction]:
        transactions = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                txn = Transaction(
                    id=row['id'],
                    reference_id=row.get('reference_id') or None,
                    amount=Decimal(row['amount']),
                    currency=row['currency'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata={k: v for k, v in row.items() if k not in ['id', 'reference_id', 'amount', 'currency', 'timestamp']}
                )
                transactions.append(txn)
        return transactions
    
    @staticmethod
    def load_bank_entries_csv(filepath: Path) -> List[BankEntry]:
        entries = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = BankEntry(
                    id=row['id'],
                    reference_id=row.get('reference_id') or None,
                    amount=Decimal(row['amount']),
                    currency=row['currency'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata={k: v for k, v in row.items() if k not in ['id', 'reference_id', 'amount', 'currency', 'timestamp']}
                )
                entries.append(entry)
        return entries
