import random
from datetime import datetime, timedelta
from test_data_generator.scenarios.base import (
    TxnIdGenerator, BankIdGenerator, add_business_days, random_business_hour,
    calculate_fee
)
from test_data_generator.config import PERIOD_START, PERIOD_END


def make_g3_duplicate(txn_id_gen=None, bank_id_gen=None):
    if txn_id_gen is None:
        txn_id_gen = TxnIdGenerator(7001)
    if bank_id_gen is None:
        bank_id_gen = BankIdGenerator(7001)
    
    merchant_id = "MCH-003"
    amount_cents = 8750
    fee_cents = calculate_fee(amount_cents)
    net_amount_cents = amount_cents - fee_cents
    
    txn_date = PERIOD_START + timedelta(days=15)
    initiated_at = random_business_hour(txn_date)
    settlement_date = add_business_days(txn_date, 1)
    
    txn_id = txn_id_gen.next()
    external_ref_id = f"REF-{txn_id.split('-')[1]}"
    
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
        "notes": "G3: duplicate bank entry scenario",
    }
    
    bank_ref_orig = bank_id_gen.next()
    bank_row_original = {
        "bank_ref_id": bank_ref_orig,
        "value_date": settlement_date.isoformat(),
        "posting_date": settlement_date.isoformat(),
        "amount_cents": net_amount_cents,
        "description": f"SETTLE {external_ref_id} {merchant_id}",
        "counterparty_ref": external_ref_id,
        "notes": "G3: original bank entry",
    }
    
    bank_ref_dup = bank_id_gen.next()
    duplicate_posting_date = settlement_date + timedelta(days=1)
    bank_row_duplicate = {
        "bank_ref_id": bank_ref_dup,
        "value_date": duplicate_posting_date.isoformat(),
        "posting_date": duplicate_posting_date.isoformat(),
        "amount_cents": net_amount_cents,
        "description": f"SETTLE {external_ref_id} {merchant_id}",
        "counterparty_ref": external_ref_id,
        "notes": "G3: duplicate bank entry",
    }
    
    return platform_row, bank_row_original, bank_row_duplicate
