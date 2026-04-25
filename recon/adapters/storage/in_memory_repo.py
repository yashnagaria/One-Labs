from typing import List

from recon.domain.models import MatchResult, MismatchResult
from recon.ports import Repository


class InMemoryRepository(Repository):
    def __init__(self):
        self._matches: List[MatchResult] = []
        self._mismatches: List[MismatchResult] = []
    
    def save_results(
        self,
        matches: List[MatchResult],
        mismatches: List[MismatchResult]
    ) -> None:
        self._matches = list(matches)
        self._mismatches = list(mismatches)
    
    def get_matches(self) -> List[MatchResult]:
        return list(self._matches)
    
    def get_mismatches(self) -> List[MismatchResult]:
        return list(self._mismatches)
    
    def clear(self) -> None:
        self._matches = []
        self._mismatches = []
