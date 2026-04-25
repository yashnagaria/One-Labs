import random
from datetime import datetime, timedelta
from decimal import Decimal
import math

from test_data_generator.config import (
    SETTLEMENT_DAYS,
    BUSINESS_HOURS_START,
    BUSINESS_HOURS_END,
    FEE_RATE_PERCENT,
)


def is_weekend(date_obj):
    return date_obj.weekday() >= 5


def add_business_days(start_date, days):
    current = start_date
    business_days_added = 0
    while business_days_added < days:
        current += timedelta(days=1)
        if not is_weekend(current):
            business_days_added += 1
    return current


def random_business_hour(date_obj):
    hour = random.randint(BUSINESS_HOURS_START, BUSINESS_HOURS_END - 1)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute, second)


def poisson_sample(rate):
    L = math.exp(-rate)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def normal_sample(mean, stddev=0.2):
    std_amount = mean * stddev
    sample = random.gauss(mean, std_amount)
    return max(int(sample), 100)


def calculate_fee(amount_cents):
    fee_exact = amount_cents * (FEE_RATE_PERCENT / 100)
    return int(math.floor(fee_exact))


class TxnIdGenerator:
    def __init__(self, start=1):
        self.current = start
    
    def next(self):
        txn_id = f"TXN-{self.current:04d}"
        self.current += 1
        return txn_id


class BankIdGenerator:
    def __init__(self, start=1):
        self.current = start
    
    def next(self):
        bank_id = f"BANK-{self.current:04d}"
        self.current += 1
        return bank_id


def make_transaction(txn_id_gen, bank_id_gen, merchant, initiated_at, amount_cents=None):
    if amount_cents is None:
        amount_cents = normal_sample(merchant["avg_amount_cents"])
    
    fee_cents = calculate_fee(amount_cents)
    net_amount_cents = amount_cents - fee_cents
    
    settlement_days = random.randint(*SETTLEMENT_DAYS["card"])
    settlement_date = add_business_days(initiated_at.date(), settlement_days)
    
    txn_id = txn_id_gen.next()
    external_ref_id = f"REF-{txn_id.split('-')[1]}"
    bank_ref_id = bank_id_gen.next()
    
    platform_row = {
        "platform_txn_id": txn_id,
        "external_ref_id": external_ref_id,
        "merchant_id": merchant["id"],
        "amount_cents": amount_cents,
        "fee_cents": fee_cents,
        "net_amount_cents": net_amount_cents,
        "status": "settled",
        "initiated_at": initiated_at.isoformat(),
        "expected_settlement_date": settlement_date.isoformat(),
        "payment_method": "card",
        "notes": "",
    }
    
    bank_row = {
        "bank_ref_id": bank_ref_id,
        "value_date": settlement_date.isoformat(),
        "posting_date": settlement_date.isoformat(),
        "amount_cents": net_amount_cents,
        "description": f"SETTLE {external_ref_id} {merchant['id']}",
        "counterparty_ref": external_ref_id,
        "notes": "",
    }
    
    return platform_row, bank_row
