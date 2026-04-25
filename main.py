#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from recon.adapters.batch.runner import BatchRunner
from recon.adapters.storage.in_memory_repo import InMemoryRepository


def main():
    parser = argparse.ArgumentParser(
        description="Reconciliation MVP - Batch Processing"
    )
    parser.add_argument(
        "--transactions",
        "-t",
        type=Path,
        required=True,
        help="Path to transactions CSV file"
    )
    parser.add_argument(
        "--bank-entries",
        "-b",
        type=Path,
        required=True,
        help="Path to bank entries CSV file"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("reconciliation_result.json"),
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    if not args.transactions.exists():
        print(f"Error: Transactions file not found: {args.transactions}", file=sys.stderr)
        sys.exit(1)
    
    if not args.bank_entries.exists():
        print(f"Error: Bank entries file not found: {args.bank_entries}", file=sys.stderr)
        sys.exit(1)
    
    repository = InMemoryRepository()
    runner = BatchRunner(repository=repository)
    
    result = runner.run(
        transactions_path=args.transactions,
        bank_entries_path=args.bank_entries,
        output_path=args.output
    )
    
    print(f"\n=== Reconciliation Summary ===")
    print(f"Total Transactions: {result.stats['total_transactions']}")
    print(f"Total Bank Entries: {result.stats['total_bank_entries']}")
    print(f"Total Matches: {result.stats['total_matches']}")
    print(f"  - Exact: {result.stats['exact_matches']}")
    print(f"  - Probable: {result.stats['probable_matches']}")
    print(f"  - Low Confidence: {result.stats['low_confidence_matches']}")
    print(f"Unmatched Transactions: {result.stats['unmatched_transactions']}")
    print(f"Unmatched Bank Entries: {result.stats['unmatched_bank_entries']}")
    print(f"\nOutput saved to: {args.output}")


if __name__ == "__main__":
    main()
