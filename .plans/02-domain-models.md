# Domain Model Specification

**Date:** March 2, 2024  
**Status:** Approved for Implementation  
**Depends On:** 01-architecture.md

## Philosophy

Domain models are **pure data structures**. No business logic, no methods, no side effects. This ensures:
- Easy serialization/deserialization
- Thread safety  
- Predictable behavior
- Simple testing

## Entities

### Transaction

Represents a platform-side transaction (charge to customer).

```python
@dataclass(frozen=True)
class Transaction:
    id: str                    # Unique identifier (e.g., "TXN-0001")
    reference_id: Optional[str]  # External reference echoed by bank
    amount: Decimal            # Gross amount (positive)
    currency: str              # ISO currency code (e.g., "USD")
    timestamp: datetime        # Initiated timestamp
    metadata: dict             # Additional fields (merchant_id, etc.)
```

**Constraints:**
- `amount` must be positive (> 0)
- `id` must be unique within batch
- `reference_id` may be null (cash transactions)

### BankEntry

Represents a bank-side record (credit or debit).

```python
@dataclass(frozen=True)
class BankEntry:
    id: str                    # Unique bank reference
    reference_id: Optional[str]  # Counterparty reference from platform
    amount: Decimal            # Net amount (can be negative for refunds)
    currency: str              # ISO currency code
    timestamp: datetime        # Value date / posting date
    metadata: dict             # Description, posting_date, etc.
```

**Constraints:**
- `amount` can be negative (refunds/debits) - **CHANGED FROM ORIGINAL SPEC**
- `id` must be unique
- `reference_id` may be null (orphan transactions)

### MatchResult

Represents a successful match between Transaction and BankEntry.

```python
@dataclass(frozen=True)
class MatchResult:
    transaction_id: str
    bank_entry_id: str
    score: float               # 0.0 to 1.0
    classification: MatchClassification
    matcher_used: str          # Which algorithm matched
    reason: str                # Human-readable explanation
```

**Score Interpretation:**
- 1.0 = Perfect match (exact reference, amount, time)
- 0.8-0.99 = Strong match (small time/amount variance)
- 0.6-0.79 = Probable match (larger variance)
- <0.6 = Low confidence (should not auto-accept)

### MismatchResult

Represents an unmatched record requiring attention.

```python
@dataclass(frozen=True)
class MismatchResult:
    type: MismatchType
    transaction_id: Optional[str]
    bank_entry_id: Optional[str]
    details: str               # Description of mismatch
```

**Types:**
- `MISSING_IN_BANK` - Platform transaction has no bank entry
- `MISSING_IN_PLATFORM` - Bank entry has no platform transaction

## Enumerations

### MatchClassification

```python
class MatchClassification(str, Enum):
    EXACT_MATCH = "exact_match"      # Score >= 0.9, exact reference match
    PROBABLE_MATCH = "probable_match" # Score 0.6-0.9, fuzzy match
    LOW_CONFIDENCE = "low_confidence" # Score < 0.6, manual review needed
```

### MismatchType

```python
class MismatchType(str, Enum):
    MISSING_IN_BANK = "missing_in_bank"         # Platform record unmatched
    MISSING_IN_PLATFORM = "missing_in_platform" # Bank record unmatched
```

## Validation Rules

1. **Amount Precision**: Use `Decimal`, never `float`
2. **Currency Consistency**: Matching only within same currency
3. **Timestamp Format**: ISO 8601 with timezone
4. **ID Uniqueness**: Enforced at batch load time

## Serialization

Models must serialize to/from:
- CSV (for batch processing)
- JSON (for API/output)
- Database rows (future)

## Future Extensions

Potential additions (not in MVP):
- `Batch` entity for ACH settlements
- `FeeBreakdown` for complex fee structures
- `Dispute` entity for chargebacks
- `Adjustment` entity for corrections

---

**Open Questions:**
1. Should we store original vs. normalized amounts? (Decision: Original only)
2. How handle partial refunds? (Decision: Future phase)
3. Multi-currency matching? (Decision: Must match same currency)

**Decisions:**
- 2024-03-02: BankEntry.amount can be negative (supports refunds)
- 2024-03-02: Frozen dataclasses prevent accidental mutation
- 2024-03-02: metadata dict for extensibility without schema changes
