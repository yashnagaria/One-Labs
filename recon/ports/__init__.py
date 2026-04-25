from abc import ABC, abstractmethod
from typing import List, Optional

from recon.domain.models import Transaction, BankEntry, MatchResult, MismatchResult


class Matcher(ABC):
    @abstractmethod
    def match(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry],
        excluded_bank_ids: set = None
    ) -> List[MatchResult]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class Scorer(ABC):
    @abstractmethod
    def calculate_score(
        self,
        transaction: Transaction,
        bank_entry: BankEntry
    ) -> float:
        pass


class Classifier(ABC):
    @abstractmethod
    def classify(self, score: float) -> MatchClassification:
        pass


class Repository(ABC):
    @abstractmethod
    def save_results(
        self,
        matches: List[MatchResult],
        mismatches: List[MismatchResult]
    ) -> None:
        pass
    
    @abstractmethod
    def get_matches(self) -> List[MatchResult]:
        pass
    
    @abstractmethod
    def get_mismatches(self) -> List[MismatchResult]:
        pass
