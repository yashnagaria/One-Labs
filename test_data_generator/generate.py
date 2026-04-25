#!/usr/bin/env python3
import csv
import json
import random
from datetime import timedelta
from pathlib import Path

from test_data_generator.config import (
    PERIOD_START, PERIOD_END, TOTAL_CLEAN_TRANSACTIONS, ROUNDING_TXN_COUNT, RANDOM_SEED
)
from test_data_generator.merchants import MERCHANTS
from test_data_generator.scenarios.base import (
    TxnIdGenerator, BankIdGenerator, is_weekend, poisson_sample, normal_sample,
    random_business_hour, make_transaction
)
from test_data_generator.scenarios.g1_cross_month import make_g1_cross_month
from test_data_generator.scenarios.g2_rounding import make_g2_rounding_batch
from test_data_generator.scenarios.g3_duplicate import make_g3_duplicate
from test_data_generator.scenarios.g4_orphan_refund import make_g4_orphan_refund


def get_all_dates(start_date, end_date):
    dates = []
    current = start_date
    while current <= end_date:
        if not is_weekend(current):
            dates.append(current)
        current += timedelta(days=1)
    return dates


def write_csv(filepath, rows, fieldnames):
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_gap_manifest(gap_data, filepath):
    with open(filepath, 'w') as f:
        json.dump(gap_data, f, indent=2)


def main():
    random.seed(RANDOM_SEED)
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    txn_id_gen = TxnIdGenerator(1)
    bank_id_gen = BankIdGenerator(1)
    
    platform_rows = []
    bank_rows = []
    
    business_days = get_all_dates(PERIOD_START, PERIOD_END)
    
    target_per_merchant = TOTAL_CLEAN_TRANSACTIONS // len(MERCHANTS)
    
    for merchant in MERCHANTS:
        generated = 0
        for day in business_days:
            if generated >= target_per_merchant:
                break
            
            num_txns = poisson_sample(merchant["daily_txn_rate"])
            
            for _ in range(num_txns):
                if generated >= target_per_merchant:
                    break
                
                amount_cents = normal_sample(merchant["avg_amount_cents"])
                initiated_at = random_business_hour(day)
                
                p, b = make_transaction(txn_id_gen, bank_id_gen, merchant, initiated_at, amount_cents)
                platform_rows.append(p)
                bank_rows.append(b)
                generated += 1
    
    p_g1, b_g1 = make_g1_cross_month()
    platform_rows.append(p_g1)
    
    g2_pairs = make_g2_rounding_batch(ROUNDING_TXN_COUNT)
    g2_platform_ids = []
    for p_g2, b_g2 in g2_pairs:
        platform_rows.append(p_g2)
        bank_rows.append(b_g2)
        g2_platform_ids.append(p_g2["platform_txn_id"])
    
    p_g3, b_g3_orig, b_g3_dup = make_g3_duplicate()
    platform_rows.append(p_g3)
    bank_rows.append(b_g3_orig)
    bank_rows.append(b_g3_dup)
    
    b_g4 = make_g4_orphan_refund()
    bank_rows.append(b_g4)
    
    random.shuffle(platform_rows)
    random.shuffle(bank_rows)
    
    platform_fields = [
        "platform_txn_id", "external_ref_id", "merchant_id", "amount_cents",
        "fee_cents", "net_amount_cents", "status", "initiated_at",
        "expected_settlement_date", "payment_method", "notes"
    ]
    write_csv(output_dir / "platform_transactions.csv", platform_rows, platform_fields)
    
    bank_fields = [
        "bank_ref_id", "value_date", "posting_date", "amount_cents",
        "description", "counterparty_ref", "notes"
    ]
    write_csv(output_dir / "bank_statement.csv", bank_rows, bank_fields)
    
    gap_manifest = {
        "period": "2024-03",
        "generated_at": "2024-03-test-data",
        "gaps": [
            {
                "gap_id": "G1",
                "type": "cross_month_settlement",
                "expected_status": "platform_only",
                "platform_txn_id": p_g1["platform_txn_id"],
                "bank_ref_id": None,
                "note": "Bank line appears in April — outside recon window"
            },
            {
                "gap_id": "G2",
                "type": "rounding_accumulation",
                "expected_status": "matched_with_delta",
                "platform_txn_ids": g2_platform_ids,
                "per_txn_delta_cents": 1,
                "aggregate_delta_cents": ROUNDING_TXN_COUNT,
                "note": "Each txn matches individually; delta only visible in rollup"
            },
            {
                "gap_id": "G3",
                "type": "duplicate_bank_entry",
                "expected_status": "bank_only",
                "platform_txn_id": p_g3["platform_txn_id"],
                "original_bank_ref": b_g3_orig["bank_ref_id"],
                "duplicate_bank_ref": b_g3_dup["bank_ref_id"],
                "note": "Same amount + counterparty_ref within 1 day"
            },
            {
                "gap_id": "G4",
                "type": "orphan_refund",
                "expected_status": "bank_only",
                "bank_ref_id": b_g4["bank_ref_id"],
                "amount_cents": b_g4["amount_cents"],
                "match_confidence": 0,
                "note": "No counterparty_ref; negative amount; no platform record"
            }
        ],
        "stats": {
            "total_platform_transactions": len(platform_rows),
            "total_bank_entries": len(bank_rows),
            "clean_matched_pairs": len(platform_rows) - 1 - ROUNDING_TXN_COUNT - 1,
            "gap_transactions": ROUNDING_TXN_COUNT + 1 + 1,
            "gap_bank_entries": ROUNDING_TXN_COUNT + 2 + 1
        }
    }
    write_gap_manifest(gap_manifest, output_dir / "gap_manifest.json")
    
    print(f"Generated {len(platform_rows)} platform transactions")
    print(f"Generated {len(bank_rows)} bank entries")
    print()
    print("Gap scenarios planted:")
    print(f"  G1 (cross-month): 1 platform txn, 0 bank entries (bank in April)")
    print(f"  G2 (rounding): {ROUNDING_TXN_COUNT} pairs with 1-cent deltas")
    print(f"  G3 (duplicate): 1 platform txn, 2 bank entries (1 extra)")
    print(f"  G4 (orphan refund): 0 platform txn, 1 bank entry")
    print()
    print("Expected reconciliation results:")
    print(f"  Matched: {len(platform_rows) - 2} (all except G1 platform + G4 bank)")
    print(f"  Platform-only: 1 (G1)")
    print(f"  Bank-only: 2 (G3 duplicate + G4 orphan)")
    print()
    print("Output files:")
    print(f"  {output_dir}/platform_transactions.csv")
    print(f"  {output_dir}/bank_statement.csv")
    print(f"  {output_dir}/gap_manifest.json")


if __name__ == "__main__":
    main()
