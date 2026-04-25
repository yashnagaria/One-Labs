import random
from datetime import datetime, timedelta
from test_data_generator.scenarios.base import (
    TxnIdGenerator, BankIdGenerator, add_business_days, random_business_hour
)
from test_data_generator.config import PERIOD_END


def make_g1_cross_month(txn_id_gen=None, bank_id_gen=None):
    if txn_id_gen is None:
        txn_id_gen = TxnIdGenerator(9001)
    if bank_id_gen is None:
        bank_id_gen = BankIdGenerator(9001)
    
    merchant_id = "MCH-001"
    amount_cents = 5000
    fee_cents = int(amount_cents * 0.029)
    net_amount_cents = amount_cents - fee_cents
    
    initiated_at = random_business_hour(PERIOD_END)
    settlement_date = add_business_days(PERIOD_END, 1)
    
    txn_id = txn_id_gen.next()
    external_ref_id = f"REF-{txn_id.split('-')[1]}"
    bank_ref_id = bank_id_gen.next()
    
    platform_row = {
        "platform_txn_id": txn_id,
        "external_ref_id": external_ref_id,
        "merchant_id": merchant_id,
        "amount_cents": amount_cents,
        "fee_cents": fee_cents,
        "net_amount_cents": net_amount_cents,
        "status": "settled",
        "initiated_at": initiated_at.isoformat(),
        "expected_settlement_date": settlement_date.isoformat(),
        "payment_method": "card",
        "notes": "G1: cross-month settlement",
    }
    
    bank_row = {
        "bank_ref_id": bank_ref_id,
        "value_date": settlement_date.isoformat(),
        "posting_date": settlement_date.isoformat(),
        "amount_cents": net_amount_cents,
        "description": f"SETTLE {external_ref_id} {merchant_id}",
        "counterparty_ref": external_ref_id,
        "notes": "G1: cross-month settlement (appears in April)",
    }
    
    return platform_row, bank_row
