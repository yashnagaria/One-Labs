# Test Data Generator Specification

**Date:** March 4, 2024  
**Status:** Approved for Implementation  
**Depends On:** 02-domain-models.md

## Purpose

Generate realistic test data with known "gap scenarios" planted. This allows us to:
1. Validate the reconciliation engine finds expected gaps
2. Measure precision/recall against ground truth
3. Test edge cases systematically

## Data Model

### Platform Transaction CSV

```csv
platform_txn_id,external_ref_id,merchant_id,amount_cents,fee_cents,net_amount_cents,status,initiated_at,expected_settlement_date,payment_method,notes
```

**Fields:**
- `amount_cents`: Gross charge amount (integer)
- `fee_cents`: Platform fee, rounded DOWN
- `net_amount_cents`: What merchant receives (= amount - fee)
- `initiated_at`: ISO8601 timestamp with timezone
- `expected_settlement_date`: T+1 or T+2 business days

### Bank Statement CSV

```csv
bank_ref_id,value_date,posting_date,amount_cents,description,counterparty_ref,notes
```

**Fields:**
- `amount_cents`: Net credit amount (can be negative for debits)
- `value_date`: When funds available
- `posting_date`: When entry posted (may differ from value_date)
- `counterparty_ref`: Echo of platform's external_ref_id

## Gap Scenarios

### G1: Cross-Month Settlement

**Setup:**
- Platform transaction on 2024-03-31 (last day of period)
- Settlement T+1 = 2024-04-01 (next month)

**Files:**
- Platform CSV: Includes TXN-9001
- Bank CSV: Does NOT include corresponding bank entry

**Expected Detection:**
- MISSING_IN_BANK for TXN-9001
- Will appear as MISSING_IN_PLATFORM in April reconciliation

### G2: Rounding Accumulation

**Setup:**
- 12 transactions with fees that round to X.5 cents
- Platform rounds DOWN (floor)
- Bank rounds UP (ceiling)
- Per-transaction delta: 1 cent (within tolerance)
- Aggregate delta: 12 cents

**Calculation:**
```python
# Target: fee_exact = N + 0.5 cents
# amount = (N + 0.5) / 0.029

# Example: N=50
# amount = 50.5 / 0.029 = 1741 cents ($17.41)
# fee_exact = 1741 * 0.029 = 50.489 ≈ 50.5

# Platform: floor(50.5) = 50 cents
# Bank: ceil(50.5) = 51 cents
# Delta: 1 cent per transaction
```

**Expected Detection:**
- All 12 match individually (delta ≤ 1¢ tolerance)
- Merchant rollup shows $0.12 discrepancy

### G3: Duplicate Bank Entry

**Setup:**
- 1 platform transaction
- 2 bank entries with:
  - Different bank_ref_id
  - Same amount
  - Same counterparty_ref
  - Posting dates within 1 day

**Expected Detection:**
- First bank entry matches platform transaction
- Second bank entry flagged as MISSING_IN_PLATFORM + DUPLICATE_CANDIDATE

### G4: Orphan Refund

**Setup:**
- Bank entry with:
  - Negative amount (debit)
  - No counterparty_ref (blank)
  - Description: "REFUND ADJUSTMENT"
- No corresponding platform transaction

**Expected Detection:**
- MISSING_IN_PLATFORM
- Match confidence: 0 (no reference, negative amount)
- Routes to manual review queue

## Merchant Population

```python
MERCHANTS = [
    {"id": "MCH-001", "name": "Apex Retail", "avg_amount_cents": 4500, "daily_txn_rate": 8},
    {"id": "MCH-002", "name": "Bolt SaaS", "avg_amount_cents": 9900, "daily_txn_rate": 4},
    {"id": "MCH-003", "name": "Cedar Eats", "avg_amount_cents": 2200, "daily_txn_rate": 12},
    {"id": "MCH-004", "name": "Drift Travel", "avg_amount_cents": 32000, "daily_txn_rate": 2},
    {"id": "MCH-005", "name": "Echo Electronics", "avg_amount_cents": 15000, "daily_txn_rate": 3},
]
```

## Volume Targets

- **Clean transactions:** ~185 (before gap injection)
- **Gap transactions:** 1 (G1) + 12 (G2) + 1 (G3) + 0 (G4) = 14
- **Total platform records:** ~199
- **Total bank records:** ~200 (includes G3 duplicate + G4 orphan)

## Generation Algorithm

```python
def generate():
    # 1. Generate clean base transactions
    for merchant in MERCHANTS:
        for business_day in march_2024:
            for _ in range(poisson(merchant.daily_txn_rate)):
                amount = normal(merchant.avg_amount, stddev=0.2)
                txn, bank = make_clean_pair(merchant, date, amount)
                platform_rows.append(txn)
                bank_rows.append(bank)
    
    # 2. Inject gap scenarios
    platform_rows.append(make_g1_platform())
    # G1 bank row goes to April file (not March)
    
    for txn, bank in make_g2_batch(12):
        platform_rows.append(txn)
        bank_rows.append(bank)
    
    platform, bank1, bank2 = make_g3_duplicate()
    platform_rows.append(platform)
    bank_rows.extend([bank1, bank2])
    
    bank_rows.append(make_g4_orphan())
    
    # 3. Shuffle to remove insertion order hints
    shuffle(platform_rows)
    shuffle(bank_rows)
    
    # 4. Write CSVs
    write_csv("platform_transactions.csv", platform_rows)
    write_csv("bank_statement.csv", bank_rows)
    
    # 5. Write gap manifest (ground truth)
    write_json("gap_manifest.json", {
        "gaps": [
            {"id": "G1", "type": "cross_month", "platform_txn_id": "TXN-9001"},
            {"id": "G2", "type": "rounding", "count": 12, "delta_cents": 12},
            {"id": "G3", "type": "duplicate", "platform_txn_id": "TXN-7001"},
            {"id": "G4", "type": "orphan_refund", "bank_ref_id": "BANK-6001"},
        ]
    })
```

## Validation Script

After generating data, run validation:

```python
def validate():
    txns = load_platform_csv()
    bank = load_bank_csv()
    manifest = load_gap_manifest()
    
    result = reconcile(txns, bank)
    
    # Check each gap was detected correctly
    for gap in manifest.gaps:
        assert_gap_detected_correctly(gap, result)
    
    print("All gaps detected as expected!")
```

## Seed for Reproducibility

```python
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
```

This ensures the same data is generated every run, making tests deterministic.

---

**Decisions:**
- 2024-03-04: Integer cents only, no floats
- 2024-03-04: 5 merchants with varying volume profiles
- 2024-03-04: G2 uses 12 transactions to accumulate meaningful delta
- 2024-03-04: Shuffle rows to prevent order-based cheating in algorithms
