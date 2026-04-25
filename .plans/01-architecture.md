# Reconciliation MVP - High-Level Architecture Plan

**Date:** March 1, 2024  
**Status:** Draft - Ready for Review  
**Author:** Engineering Team

## Overview

We need to build a reliable, explainable, and extensible reconciliation system for matching platform transactions with bank entries. This document outlines the architectural approach before implementation begins.

## Goals

1. **Deterministic matching first** - Always prioritize exact matching over fuzzy
2. **Confidence-based decisions** - Avoid auto-accepting low-confidence matches  
3. **Explainability** - Every result must include why it matched
4. **Idempotency** - Same input produces same output
5. **Event-driven ready** - Core logic isolated from input/output adapters

## Architectural Style: Hexagonal (Ports & Adapters)

```
                    ┌─────────────────┐
     Input ───────▶ │                 │
    (CSV/Event)     │   Core Domain   │ ────▶ Output (JSON/DB)
                    │   (Stateless)   │
                    │                 │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
           Matchers      Scorers      Classifiers
```

## Core Components

### 1. Domain Models (Pure Data)
- Transaction
- BankEntry  
- MatchResult
- MismatchResult
- Enums: MatchClassification, MismatchType

**Constraint:** Immutable dataclasses only. No business logic.

### 2. Ports (Abstract Interfaces)
- `Matcher` - Matching strategy contract
- `Scorer` - Confidence scoring contract  
- `Classifier` - Score → label mapping contract
- `Repository` - Persistence contract

### 3. Services (Business Logic)
- `MatchingEngine` - Orchestrates matchers and scoring
- `MismatchDetector` - Identifies unmatched records

### 4. Use Cases (Application Layer)
- `ReconcileUseCase` - Main workflow coordinator

### 5. Adapters (I/O)
- Batch: CSV loader, batch runner
- Storage: InMemoryRepo (MVP), DBRepo (future)
- Event: Consumer/Producer (future)

## Matching Strategy

### Phase 1: Exact Matching (Reference ID)
- Match by `reference_id` + exact amount + currency
- Time window: ±48 hours (configurable)
- Score: 1.0
- Classification: EXACT_MATCH

### Phase 2: Fuzzy Matching (Amount + Time)
- For unmatched transactions
- Score based on:
  - Amount similarity (50% weight)
  - Time proximity (30% weight)  
  - Reference similarity (20% weight)
- Minimum threshold: 0.5
- Classification thresholds:
  - ≥0.9: EXACT_MATCH
  - 0.6-0.9: PROBABLE_MATCH
  - <0.6: LOW_CONFIDENCE

## Edge Cases to Handle

| Scenario | Handling |
|----------|----------|
| Time delays | Configurable time window |
| Rounding errors | Amount tolerance (1¢ default) |
| Missing reference_id | Fall back to fuzzy |
| Duplicate transactions | Detect via same keys |
| Late data | Re-runnable pipeline |
| Cross-month settlement | Detect as platform-only |
| Negative amounts (refunds) | Allow in BankEntry |

## Scalability Approach

### MVP (Now)
- In-memory processing
- Daily batch jobs
- CSV input/output
- ~200 transactions/day

### Future (Post-MVP)
- Columnar storage (Parquet/BigQuery)
- Indexed joins
- Distributed processing (Spark)
- Real-time event streaming

## Testing Strategy

1. **Unit Tests**
   - Individual matchers
   - Scorer algorithms
   - Classification logic

2. **Integration Tests**
   - End-to-end reconciliation
   - Gap scenario validation

3. **Edge Case Tests**
   - Boundary conditions
   - Duplicate detection
   - Missing data handling

## Success Criteria

- [ ] Correctly identifies exact matches (reference_id)
- [ ] Correctly identifies probable matches (fuzzy)
- [ ] Flags unmatched transactions (missing_in_bank)
- [ ] Flags unmatched bank entries (missing_in_platform)
- [ ] Handles rounding deltas at individual and aggregate levels
- [ ] Provides explainable match reasons
- [ ] Completes in <1s for 200 transactions

## Next Steps

1. Review architecture with team
2. Approve domain model design
3. Begin implementation of core components
4. Build test data generator for validation

---

**Decision Log:**
- 2024-03-01: Chose hexagonal architecture for testability
- 2024-03-01: Selected deterministic-first matching strategy
- 2024-03-01: Decided on immutable dataclasses for domain
