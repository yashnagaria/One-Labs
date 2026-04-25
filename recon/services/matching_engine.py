from recon.domain.models import (
    Transaction,
    BankEntry,
    MatchResult,
    MatchClassification,
)
from recon.ports import Matcher, Scorer, Classifier
from recon.implementations.matchers.reference_id import ReferenceIdMatcher
from recon.implementations.scorers.weighted_scorer import WeightedScorer
from recon.implementations.classifiers.threshold_classifier import ThresholdClassifier
from typing import List


class MatchingEngine:
    def __init__(
        self,
        matchers: List[Matcher] = None,
        scorer: Scorer = None,
        classifier: Classifier = None
    ):
        self.matchers = matchers or [
            ReferenceIdMatcher(),
        ]
        self.scorer = scorer or WeightedScorer()
        self.classifier = classifier or ThresholdClassifier()
    
    def match(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry]
    ) -> List[MatchResult]:
        results = []
        matched_bank_ids = set()
        
        for matcher in self.matchers:
            matches = matcher.match(
                transactions,
                bank_entries,
                excluded_bank_ids=matched_bank_ids
            )
            
            for match in matches:
                matched_bank_ids.add(match.bank_entry_id)
                results.append(match)
        
        unmatched_transactions = [
            t for t in transactions
            if t.id not in {r.transaction_id for r in results}
        ]
        
        fuzzy_matches = self._fuzzy_match(
            unmatched_transactions,
            bank_entries,
            matched_bank_ids
        )
        results.extend(fuzzy_matches)
        
        return results
    
    def _fuzzy_match(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry],
        excluded_bank_ids: set
    ) -> List[MatchResult]:
        results = []
        matched_bank_ids = set(excluded_bank_ids)
        
        for txn in transactions:
            best_match = None
            best_score = 0.0
            
            for entry in bank_entries:
                if entry.id in matched_bank_ids:
                    continue
                
                if txn.currency != entry.currency:
                    continue
                
                score = self.scorer.calculate_score(txn, entry)
                
                if score > best_score and score >= 0.5:
                    best_score = score
                    best_match = entry
            
            if best_match:
                classification = self.classifier.classify(best_score)
                results.append(MatchResult(
                    transaction_id=txn.id,
                    bank_entry_id=best_match.id,
                    score=best_score,
                    classification=classification,
                    matcher_used="fuzzy_amount_time",
                    reason=f"Amount match with score {best_score:.2f}"
                ))
                matched_bank_ids.add(best_match.id)
        
        return results
