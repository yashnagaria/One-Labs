import json
from pathlib import Path
from typing import List, Optional

from recon.adapters.batch.loader import DataLoader
from recon.adapters.storage.in_memory_repo import InMemoryRepository
from recon.usecases.reconcile import ReconcileUseCase, ReconciliationResult


class BatchRunner:
    def __init__(
        self,
        use_case: Optional[ReconcileUseCase] = None,
        repository: Optional[InMemoryRepository] = None
    ):
        self.use_case = use_case or ReconcileUseCase(repository=repository)
        self.repository = repository
    
    def run(
        self,
        transactions_path: Path,
        bank_entries_path: Path,
        output_path: Optional[Path] = None
    ) -> ReconciliationResult:
        transactions = DataLoader.load_transactions_csv(transactions_path)
        bank_entries = DataLoader.load_bank_entries_csv(bank_entries_path)
        
        result = self.use_case.execute(transactions, bank_entries)
        
        if output_path:
            self._save_output(result, output_path)
        
        return result
    
    def _save_output(self, result: ReconciliationResult, output_path: Path) -> None:
        output_data = {
            "stats": result.stats,
            "matches": [
                {
                    "transaction_id": m.transaction_id,
                    "bank_entry_id": m.bank_entry_id,
                    "score": m.score,
                    "classification": m.classification.value,
                    "matcher_used": m.matcher_used,
                    "reason": m.reason
                }
                for m in result.matches
            ],
            "mismatches": [
                {
                    "type": mm.type.value,
                    "transaction_id": mm.transaction_id,
                    "bank_entry_id": mm.bank_entry_id,
                    "details": mm.details
                }
                for mm in result.mismatches
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
