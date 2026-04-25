#!/usr/bin/env python3
import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from recon.domain.models import Transaction, BankEntry, MatchResult, MismatchResult
from recon.usecases.reconcile import ReconcileUseCase
from recon.adapters.storage.in_memory_repo import InMemoryRepository


def load_platform_csv(filepath):
    transactions = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            amount_dollars = Decimal(row['amount_cents']) / 100
            txn = Transaction(
                id=row['platform_txn_id'],
                reference_id=row['external_ref_id'] if row['external_ref_id'] else None,
                amount=amount_dollars,
                currency='USD',
                timestamp=datetime.fromisoformat(row['initiated_at']),
                metadata={
                    'merchant_id': row['merchant_id'],
                    'net_amount_cents': int(row['net_amount_cents']),
                    'fee_cents': int(row['fee_cents']),
                    'expected_settlement_date': row['expected_settlement_date'],
                    'notes': row.get('notes', ''),
                }
            )
            transactions.append(txn)
    return transactions


def load_bank_csv(filepath):
    entries = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            amount_dollars = Decimal(row['amount_cents']) / 100
            entry = BankEntry(
                id=row['bank_ref_id'],
                reference_id=row['counterparty_ref'] if row['counterparty_ref'] else None,
                amount=amount_dollars,
                currency='USD',
                timestamp=datetime.fromisoformat(row['value_date'] + 'T00:00:00'),
                metadata={
                    'posting_date': row['posting_date'],
                    'description': row['description'],
                    'notes': row.get('notes', ''),
                }
            )
            entries.append(entry)
    return entries


def main():
    base_dir = Path(__file__).parent
    
    print("Loading test data...")
    transactions = load_platform_csv(base_dir / "output" / "platform_transactions.csv")
    bank_entries = load_bank_csv(base_dir / "output" / "bank_statement.csv")
    
    print(f"Loaded {len(transactions)} platform transactions")
    print(f"Loaded {len(bank_entries)} bank entries")
    print()
    
    repository = InMemoryRepository()
    use_case = ReconcileUseCase(repository=repository)
    
    print("Running reconciliation...")
    result = use_case.execute(transactions, bank_entries)
    
    print()
    print("=" * 60)
    print("RECONCILIATION RESULTS")
    print("=" * 60)
    print()
    
    print("SUMMARY:")
    print(f"  Total Transactions: {result.stats['total_transactions']}")
    print(f"  Total Bank Entries: {result.stats['total_bank_entries']}")
    print(f"  Total Matches: {result.stats['total_matches']}")
    print(f"    - Exact: {result.stats['exact_matches']}")
    print(f"    - Probable: {result.stats['probable_matches']}")
    print(f"    - Low Confidence: {result.stats['low_confidence_matches']}")
    print(f"  Unmatched Transactions: {result.stats['unmatched_transactions']}")
    print(f"  Unmatched Bank Entries: {result.stats['unmatched_bank_entries']}")
    print()
    
    print("GAP SCENARIO ANALYSIS:")
    print()
    
    with open(base_dir / "output" / "gap_manifest.json") as f:
        manifest = json.load(f)
    
    matched_txn_ids = {m.transaction_id for m in result.matches}
    matched_bank_ids = {m.bank_entry_id for m in result.matches}
    
    for gap in manifest['gaps']:
        gap_id = gap['gap_id']
        gap_type = gap['type']
        
        if gap_id == 'G1':
            txn_id = gap['platform_txn_id']
            if txn_id in matched_txn_ids:
                print(f"  {gap_id} ({gap_type}): ✗ INCORRECT - matched but should be platform_only")
            else:
                print(f"  {gap_id} ({gap_type}): ✓ CORRECT - platform_only as expected")
        
        elif gap_id == 'G2':
            rounding_ids = set(gap['platform_txn_ids'])
            matched_rounding = rounding_ids.intersection(matched_txn_ids)
            if len(matched_rounding) == len(rounding_ids):
                print(f"  {gap_id} ({gap_type}): ✓ CORRECT - all 12 matched individually")
                print(f"    Aggregate delta: {gap['aggregate_delta_cents']} cents (check in rollup)")
            else:
                print(f"  {gap_id} ({gap_type}): ✗ INCORRECT - only {len(matched_rounding)}/12 matched")
        
        elif gap_id == 'G3':
            dup_bank_id = gap['duplicate_bank_ref']
            if dup_bank_id in matched_bank_ids:
                print(f"  {gap_id} ({gap_type}): ✗ INCORRECT - duplicate was matched")
            else:
                print(f"  {gap_id} ({gap_type}): ✓ CORRECT - duplicate flagged as bank_only")
        
        elif gap_id == 'G4':
            orphan_bank_id = gap['bank_ref_id']
            if orphan_bank_id in matched_bank_ids:
                print(f"  {gap_id} ({gap_type}): ✗ INCORRECT - orphan was matched")
            else:
                print(f"  {gap_id} ({gap_type}): ✓ CORRECT - orphan flagged as bank_only")
    
    print()
    print("MISMATCHES:")
    if result.mismatches:
        for mm in result.mismatches[:10]:
            if mm.type.value == 'missing_in_bank':
                print(f"  PLATFORM_ONLY: {mm.transaction_id}")
            else:
                print(f"  BANK_ONLY: {mm.bank_entry_id}")
        if len(result.mismatches) > 10:
            print(f"  ... and {len(result.mismatches) - 10} more")
    else:
        print("  None")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
