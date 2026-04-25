# Plans Index

**Last Updated:** March 5, 2024

This directory contains all planning documents for the Reconciliation MVP project. Plans are numbered in the order they were created and should be read sequentially.

## Document Guide

| # | Document | Purpose | Status |
|---|----------|---------|--------|
| 01 | [architecture.md](./01-architecture.md) | High-level architecture & design principles | Approved |
| 02 | [domain-models.md](./02-domain-models.md) | Domain entity specifications | Approved |
| 03 | [matching-engine.md](./03-matching-engine.md) | Matching algorithm & scoring | Approved |
| 04 | [mismatch-detector.md](./04-mismatch-detector.md) | Gap detection logic | Approved |
| 05 | [test-data-generator.md](./05-test-data-generator.md) | Test data generation spec | Approved |
| 06 | [implementation-roadmap.md](./06-implementation-roadmap.md) | Development timeline & tasks | Complete |

## Quick Reference

### For Understanding the System
Read in order: 01 → 02 → 03 → 04

### For Understanding Test Data
Read: 05

### For Implementation Details
Read: 06 (references all others)

## Decision Log

All major decisions are recorded in individual plan documents. Key decisions:

- **Architecture:** Hexagonal (Ports & Adapters) - Document 01
- **Domain Model:** Immutable frozen dataclasses - Document 02
- **Matching Strategy:** Deterministic first, fuzzy second - Document 03
- **BankEntry Constraint:** Allow negative amounts (refunds) - Document 02
- **Test Data:** 4 gap scenarios (G1-G4) - Document 05

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2024-03-01 | Created 01-architecture.md | Engineering |
| 2024-03-02 | Created 02-domain-models.md | Engineering |
| 2024-03-03 | Created 03-matching-engine.md | Engineering |
| 2024-03-03 | Created 04-mismatch-detector.md | Engineering |
| 2024-03-04 | Created 05-test-data-generator.md | Engineering |
| 2024-03-05 | Created 06-implementation-roadmap.md | Engineering |

## Implementation Status

**Status:** ✅ COMPLETE

All plans have been implemented as specified:
- Domain models match Document 02
- Matching engine follows Document 03
- Mismatch detection per Document 04
- Test data generator implements Document 05
- Delivered ahead of Document 06 schedule

---

**Questions?** Refer to the relevant plan document or contact the engineering team.
