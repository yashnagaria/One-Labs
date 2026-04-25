import math
import random
from datetime import datetime, timedelta
from test_data_generator.scenarios.base import (
    TxnIdGenerator, BankIdGenerator, add_business_days, random_business_hour,
    calculate_fee
)
from test_data_generator.config import PERIOD_START, PERIOD_END


def find_half_cent_amounts(count=12):
    amounts = []
    
    for n in range(30, 1450):
        amount_exact = (n + 0.5) / 0.029
        amount_cents = int(round(amount_exact))
        
        fee_exact = amount_cents * 0.029
        fractional_part = fee_exact - int(fee_exact)
        
        if 0.49 <= fractional_part <= 0.51:
            if 1000 <= amount_cents <= 50000:
                amounts.append(amount_cents)
        
        if len(amounts) >= count * 3:
            break
    
    return random.sample(amounts, min(count, len(amounts)))


def make_g2_rounding_batch(count=12, txn_id_gen=None, bank_id_gen=None, start_date=None):
    if txn_id_gen is None:
        txn_id_gen = TxnIdGenerator(8001)
    if bank_id_gen is None:
        bank_id_gen = BankIdGenerator(8001)
    
    amounts = find_half_cent_amounts(count)
    results = []
    
    if start_date is None:
        start_date = PERIOD_START + timedelta(days=10)
    
    merchant_ids = ["MCH-001", "MCH-002", "MCH-003", "MCH-004", "MCH-005"]
    
    for i, amount_cents in enumerate(amounts):
        merchant_id = merchant_ids[i % len(merchant_ids)]
        
        fee_exact = amount_cents * 0.029
        fee_platform = int(math.floor(fee_exact))
        fee_bank = int(math.ceil(fee_exact))
        
        net_platform = amount_cents - fee_platform
        net_bank = amount_cents - fee_bank
        
        date_offset = i % 5
        txn_date = start_date + timedelta(days=date_offset)
        if txn_date > PERIOD_END:
            txn_date = PERIOD_END - timedelta(days=1)
        
        initiated_at = random_business_hour(txn_date)
        settlement_date = add_business_days(txn_date, 1)
        
        txn_id = txn_id_gen.next()
        external_ref_id = f"REF-{txn_id.split('-')[1]}"
        bank_ref_id = bank_id_gen.next()
        
        platform_row = {
            "platform_txn_id": txn_id,
            "external_ref_id": external_ref_id,
            "merchant_id": merchant_id,
            "amount_cents": amount_cents,
            "fee_cents": fee_platform,
            "net_amount_cents": net_platform,
            "status": "settled",
            "initiated_at": initiated_at.isoformat(),
            "expected_settlement_date": settlement_date.isoformat(),
            "payment_method": "card",
            "notes": "G2: half-cent fee rounding",
        }
        
        bank_row = {
            "bank_ref_id": bank_ref_id,
            "value_date": settlement_date.isoformat(),
            "posting_date": settlement_date.isoformat(),
            "amount_cents": net_bank,
            "description": f"SETTLE {external_ref_id} {merchant_id}",
            "counterparty_ref": external_ref_id,
            "notes": "G2: bank rounds fee UP",
        }
        
        results.append((platform_row, bank_row))
    
    return results
