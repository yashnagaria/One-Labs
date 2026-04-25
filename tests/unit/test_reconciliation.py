import pytest
from datetime import datetime
from decimal import Decimal

from recon.domain.models import Transaction, BankEntry, MatchClassification
from recon.services.matching_engine import MatchingEngine
from recon.services.mismatch_detector import MismatchDetector
from recon.usecases.reconcile import ReconcileUseCase


class TestMatchingEngine:
    def test_exact_reference_match(self):
        txns = [
            Transaction(
                id="txn-1",
                reference_id="REF123",
                amount=Decimal("100.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            )
        ]
        
        bank_entries = [
            BankEntry(
                id="bank-1",
                reference_id="REF123",
                amount=Decimal("100.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 10, 30, 0)
            )
        ]
        
        engine = MatchingEngine()
        matches = engine.match(txns, bank_entries)
        
        assert len(matches) == 1
        assert matches[0].transaction_id == "txn-1"
        assert matches[0].bank_entry_id == "bank-1"
        assert matches[0].score == 1.0
        assert matches[0].classification == MatchClassification.EXACT_MATCH
    
    def test_fuzzy_match_by_amount(self):
        txns = [
            Transaction(
                id="txn-1",
                reference_id=None,
                amount=Decimal("250.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            )
        ]
        
        bank_entries = [
            BankEntry(
                id="bank-1",
                reference_id=None,
                amount=Decimal("250.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 10, 5, 0)
            )
        ]
        
        engine = MatchingEngine()
        matches = engine.match(txns, bank_entries)
        
        assert len(matches) == 1
        assert matches[0].score > 0.8


class TestMismatchDetector:
    def test_detect_missing_in_bank(self):
        txns = [
            Transaction(
                id="txn-1",
                reference_id="REF1",
                amount=Decimal("100.00"),
                currency="USD",
                timestamp=datetime.now()
            ),
            Transaction(
                id="txn-2",
                reference_id="REF2",
                amount=Decimal("200.00"),
                currency="USD",
                timestamp=datetime.now()
            )
        ]
        
        bank_entries = [
            BankEntry(
                id="bank-1",
                reference_id="REF1",
                amount=Decimal("100.00"),
                currency="USD",
                timestamp=datetime.now()
            )
        ]
        
        engine = MatchingEngine()
        matches = engine.match(txns, bank_entries)
        
        detector = MismatchDetector()
        mismatches = detector.detect_mismatches(txns, bank_entries, matches)
        
        assert len(mismatches) == 1
        assert mismatches[0].transaction_id == "txn-2"


class TestReconcileUseCase:
    def test_end_to_end_reconciliation(self):
        txns = [
            Transaction(
                id="txn-1",
                reference_id="REF123",
                amount=Decimal("100.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            Transaction(
                id="txn-2",
                reference_id=None,
                amount=Decimal("250.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 11, 0, 0)
            )
        ]
        
        bank_entries = [
            BankEntry(
                id="bank-1",
                reference_id="REF123",
                amount=Decimal("100.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 10, 30, 0)
            ),
            BankEntry(
                id="bank-2",
                reference_id=None,
                amount=Decimal("250.00"),
                currency="USD",
                timestamp=datetime(2024, 1, 15, 11, 5, 0)
            )
        ]
        
        use_case = ReconcileUseCase()
        result = use_case.execute(txns, bank_entries)
        
        assert result.stats["total_matches"] == 2
        assert result.stats["exact_matches"] == 1
        assert len(result.mismatches) == 0
