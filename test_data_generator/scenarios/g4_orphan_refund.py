import random
from datetime import datetime, timedelta
from test_data_generator.scenarios.base import BankIdGenerator
from test_data_generator.config import PERIOD_START, PERIOD_END


def make_g4_orphan_refund(bank_id_gen=None):
    if bank_id_gen is None:
        bank_id_gen = BankIdGenerator(6001)
    
    refund_amount_cents = -4500
    refund_date = PERIOD_START + timedelta(days=21)
    
    bank_ref_id = bank_id_gen.next()
    
    bank_row = {
        "bank_ref_id": bank_ref_id,
        "value_date": refund_date.isoformat(),
        "posting_date": refund_date.isoformat(),
        "amount_cents": refund_amount_cents,
        "description": "REFUND ADJUSTMENT",
        "counterparty_ref": "",
        "notes": "G4: orphan refund — no platform record",
    }
    
    return bank_row
