# Matching Engine Specification

**Date:** March 3, 2024  
**Status:** Approved for Implementation  
**Depends On:** 02-domain-models.md

## Purpose

The MatchingEngine orchestrates the reconciliation workflow:
1. Execute matchers in priority order
2. Apply confidence scoring
3. Apply classification thresholds
4. Prevent double-matching

## Algorithm

```
Input: List[Transaction], List[BankEntry]
Output: List[MatchResult]

1. Initialize matched_bank_ids = empty set
2. Initialize results = empty list

3. For each matcher in matchers:
   a. Call matcher.match(txns, bank_entries, matched_bank_ids)
   b. For each match in matches:
      - Add bank_entry_id to matched_bank_ids
      - Append to results

4. Find unmatched_transactions = txns not in results

5. For each unmatched transaction:
   a. Find best fuzzy match among remaining bank entries
   b. If score >= 0.5:
      - Classify score
      - Create MatchResult with "fuzzy_amount_time" matcher
      - Add to matched_bank_ids and results

6. Return results
```

## Matchers

### ReferenceIdMatcher

**Priority:** 1 (Highest)

**Logic:**
- Index bank entries by `(reference_id, amount, currency)`
- For each transaction with reference_id:
  - Lookup candidates
  - Filter by time window (±48h default)
  - Return first match (deterministic)

**Score:** Always 1.0

**Classification:** Always EXACT_MATCH

**Configuration:**
- `time_window_hours: int = 48`

### AmountTimeMatcher (Planned)

**Priority:** 2 (Not used in MVP, fuzzy handles this)

Will be implemented if needed for specific scenarios.

## Scorer: WeightedScorer

Calculates confidence score for transaction/bank entry pair.

### Formula

```
score = (amount_score * 0.5) + 
        (time_score * 0.3) + 
        (reference_score * 0.2)
```

### Amount Score

```python
if txn_amount == bank_amount:
    return 1.0

diff = abs(txn_amount - bank_amount)
max_amount = max(txn_amount, bank_amount)
diff_percent = diff / max_amount

if diff_percent > 0.05:  # 5% tolerance
    return 0.0

return 1.0 - (diff_percent / 0.05) * 0.5
```

### Time Score

```python
diff_seconds = abs(txn_time - bank_time)
max_window = 72 hours

if diff_seconds >= max_window:
    return 0.0

return 1.0 - (diff_seconds / max_window)
```

### Reference Score

```python
if txn_ref == bank_ref:
    return 1.0
if txn_ref and bank_ref and txn_ref.lower() == bank_ref.lower():
    return 0.8
return 0.0
```

## Classifier: ThresholdClassifier

Maps score to classification label.

```python
if score >= 0.9:
    return EXACT_MATCH
elif score >= 0.6:
    return PROBABLE_MATCH
else:
    return LOW_CONFIDENCE
```

**Configurable thresholds:**
- `exact_threshold: float = 0.9`
- `probable_threshold: float = 0.6`

## Determinism Guarantees

1. **Matcher order fixed** - ReferenceIdMatcher always runs before fuzzy
2. **Index ordering** - First match in index wins
3. **No randomness** - Same inputs always produce same outputs
4. **Isolation** - Matchers don't share state

## Performance Considerations

- O(N*M) worst case for fuzzy matching (N=txns, M=bank_entries)
- Indexing by reference_id reduces exact matching to O(N)
- For 200 transactions × 200 bank entries = 40k comparisons max
- Well within performance targets (<1s)

## Edge Case Handling

| Case | Behavior |
|------|----------|
| Multiple bank entries with same ref | Match first by bank entry ID order |
| Transaction with null reference | Skip exact matching, go to fuzzy |
| Zero amount | Validation error (rejected at load) |
| Negative bank amount | Allowed (refunds), fuzzy matched |
| Amount > 5% different | Score = 0 (no match possible) |

## Interface

```python
class MatchingEngine:
    def __init__(
        self,
        matchers: List[Matcher] = None,
        scorer: Scorer = None,
        classifier: Classifier = None
    )
    
    def match(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry]
    ) -> List[MatchResult]
```

## Testing Strategy

1. **Unit tests** for each scorer component
2. **Integration tests** for full matching pipeline
3. **Property-based tests** for determinism verification
4. **Edge case tests** for boundary conditions

---

**Open Questions:**
- Should we support multiple fuzzy matches per transaction? (Decision: No, one-to-one only in MVP)
- How handle currency conversion? (Decision: Must match exact currency)

**Decisions:**
- 2024-03-03: Fixed matcher order (reference first, fuzzy second)
- 2024-03-03: Score threshold at 0.5 minimum for any match
- 2024-03-03: 5% amount tolerance max for fuzzy matching
