# Mismatch Detector Specification

**Date:** March 3, 2024  
**Status:** Approved for Implementation  
**Depends On:** 02-domain-models.md

## Purpose

After matching identifies paired records, the MismatchDetector finds unmatched records requiring investigation.

## Algorithm

```
Input: List[Transaction], List[BankEntry], List[MatchResult]
Output: List[MismatchResult]

1. matched_txn_ids = {m.transaction_id for m in matches}
2. matched_bank_ids = {m.bank_entry_id for m in matches}
3. mismatches = []

4. For each transaction:
   If transaction.id not in matched_txn_ids:
      mismatches.append(MismatchResult(
         type=MISSING_IN_BANK,
         transaction_id=transaction.id,
         bank_entry_id=null,
         details="Transaction not found in bank entries"
      ))

5. For each bank entry:
   If bank_entry.id not in matched_bank_ids:
      mismatches.append(MismatchResult(
         type=MISSING_IN_PLATFORM,
         transaction_id=null,
         bank_entry_id=bank_entry.id,
         details="Bank entry not found in transactions"
      ))

6. Return mismatches
```

## Mismatch Types

### MISSING_IN_BANK

Platform has a transaction but no corresponding bank entry was found.

**Possible Causes:**
- Transaction hasn't settled yet (cross-month scenario)
- Bank delay in reporting
- Transaction failed after platform recorded it
- Data loss on bank side

**Action:** Usually "wait and retry tomorrow"

### MISSING_IN_PLATFORM

Bank has an entry but no corresponding platform transaction.

**Possible Causes:**
- Bank error (duplicate entry)
- Manual adjustment by bank
- Refund processed by bank but not recorded in platform
- Chargeback
- Fraudulent transaction

**Action:** Requires manual investigation

## Special Case: Duplicate Detection

While not a mismatch per se, duplicates should be flagged during mismatch detection:

```python
# During MISSING_IN_PLATFORM detection
if bank_entry not matched:
   # Check for duplicates
   similar_entries = find_similar_unmatched_bank_entries(bank_entry)
   if similar_entries:
      flag_as_duplicate_candidate()
```

Similarity criteria:
- Same amount
- Same counterparty_ref (if present)
- Within 1 business day

## Interface

```python
class MismatchDetector:
    def detect_mismatches(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry],
        matches: List[MatchResult]
    ) -> List[MismatchResult]
```

## Reporting Format

Each mismatch should include:

```json
{
  "type": "missing_in_bank|missing_in_platform",
  "transaction_id": "TXN-xxx|null",
  "bank_entry_id": "BANK-xxx|null",
  "details": "Human-readable description",
  "severity": "high|medium|low",
  "suggested_action": "auto_resolve|manual_review|wait_retry"
}
```

Severity heuristics:
- **High**: Large amount (> $10,000), negative bank amount (refund), no reference
- **Medium**: Moderate amount, missing reference but positive amount
- **Low**: Small amount, expected delay scenario

## Testing Scenarios

| Scenario | Expected Result |
|----------|----------------|
| All matched | Empty mismatch list |
| One unmatched txn | One MISSING_IN_BANK |
| One unmatched bank | One MISSING_IN_PLATFORM |
| Equal unmatched counts | Mixed list |
| Duplicate bank entries | Two MISSING_IN_PLATFORM with duplicate flags |

## Integration with Use Case

```python
class ReconcileUseCase:
    def execute(self, txns, bank_entries):
        matches = self.matching_engine.match(txns, bank_entries)
        mismatches = self.mismatch_detector.detect_mismatches(txns, bank_entries, matches)
        
        # Persist results
        self.repository.save_results(matches, mismatches)
        
        return ReconciliationResult(matches, mismatches, stats)
```

---

**Decisions:**
- 2024-03-03: Mismatch detection runs AFTER matching (not parallel)
- 2024-03-03: Severity scoring for prioritization
- 2024-03-03: Duplicate flagging as metadata, not separate type
