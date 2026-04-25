```markdown
# 🔍 One-Labs — Reconciliation MVP

A financial reconciliation engine that matches **platform transactions** against **bank statement entries**, surfacing exact, probable, and low-confidence matches along with unmatched records. Ships with both a CLI batch runner and an interactive Streamlit dashboard.

---

## Features

- **Multi-confidence matching** — classifies each match as Exact (≥ 0.9), Probable (0.6–0.9), or Low Confidence (< 0.6)
- **Hexagonal architecture** — domain logic is cleanly separated from adapters (CSV, in-memory repo, batch runner)
- **Streamlit dashboard** — upload CSVs, inspect matches/mismatches, and download results as JSON or CSV
- **CLI mode** — scriptable batch processing for automation pipelines
- **Test data generator** — synthetic platform + bank CSVs with configurable gap scenarios for local testing

---

## Project Structure

```
One-Labs/
├── recon/                        # Core package (hexagonal architecture)
│   ├── domain/                   # Models: Transaction, BankEntry, Match, Mismatch
│   ├── usecases/                 # ReconcileUseCase — orchestrates matching logic
│   └── adapters/
│       ├── batch/runner.py       # CLI batch runner
│       └── storage/in_memory_repo.py
├── test_data_generator/          # Generates synthetic test CSVs
├── tests/unit/                   # Pytest unit tests
├── streamlit_app.py              # Interactive dashboard
├── main.py                       # CLI entry point
├── generate_test_data.py         # Test data helper script
├── generate_data.sh              # Shell wrapper for test data generation
├── run_streamlit.sh              # Shell wrapper to launch Streamlit
├── pyproject.toml                # Build config + dependencies
└── pytest.ini                    # Pytest configuration
```

---

## Quickstart

### 1. Install

```bash
git clone https://github.com/yashnagaria/One-Labs.git
cd One-Labs
pip install -e ".[all]"
```

Requires **Python ≥ 3.10**.

### 2. Generate sample data

```bash
python test_data_generator/generate.py
# OR
bash generate_data.sh
```

This produces:
- `test_data_generator/output/platform_transactions.csv`
- `test_data_generator/output/bank_statement.csv`

### 3a. Run via CLI

```bash
python main.py \
  --transactions test_data_generator/output/platform_transactions.csv \
  --bank-entries test_data_generator/output/bank_statement.csv \
  --output reconciliation_result.json
```

**Example output:**

```
=== Reconciliation Summary ===
Total Transactions:       200
Total Bank Entries:       195
Total Matches:            185
  - Exact:                162
  - Probable:              18
  - Low Confidence:         5
Unmatched Transactions:    15
Unmatched Bank Entries:    10

Output saved to: reconciliation_result.json
```

### 3b. Run via Streamlit dashboard

```bash
bash run_streamlit.sh
# OR
streamlit run streamlit_app.py
```

Open `http://localhost:8501`, upload both CSVs, and explore:
- **Overview tab** — match confidence pie chart + summary bar chart
- **Matches tab** — filterable table with score progress bars, downloadable CSV
- **Mismatches tab** — mismatch type breakdown with pie chart
- **Export tab** — full JSON results + plain-text summary

---

## CSV Format

### Platform Transactions

| Column | Description |
|--------|-------------|
| `platform_txn_id` | Unique transaction ID |
| `external_ref_id` | Optional external reference (used for matching) |
| `merchant_id` | Merchant identifier |
| `amount_cents` | Transaction amount in cents |
| `fee_cents` | Platform fee in cents |
| `net_amount_cents` | Net amount after fee |
| `status` | Transaction status |
| `initiated_at` | ISO 8601 timestamp |
| `expected_settlement_date` | Expected settlement date |
| `payment_method` | Payment method |
| `notes` | Optional notes |

### Bank Statement

| Column | Description |
|--------|-------------|
| `bank_ref_id` | Bank reference ID |
| `value_date` | Value date (YYYY-MM-DD) |
| `posting_date` | Posting date |
| `amount_cents` | Amount in cents |
| `description` | Transaction description |
| `counterparty_ref` | Optional counterparty reference (used for matching) |
| `notes` | Optional notes |

---

## Running Tests

```bash
pytest
# With coverage:
pytest --cov=recon
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit ≥ 1.28` | Interactive dashboard |
| `pandas ≥ 2.0` | Tabular data handling |
| `plotly ≥ 5.15` | Charts and visualizations |
| `pytest`, `pytest-cov` | Testing |
| `black`, `ruff`, `mypy` | Code quality |

---

## ⚠️ Production Concerns

1. **In-memory repository does not scale.** The current `InMemoryRepository` loads all transactions and bank entries into RAM. On a real dataset (millions of records), this will OOM — the storage layer needs to be swapped for a database-backed adapter (PostgreSQL, etc.) with paginated or streaming reads.

2. **No idempotency or audit trail.** Every run re-processes the full input from scratch with no record of prior runs, match IDs, or change history. In a production reconciliation system, re-running on the same data must not create duplicate match records — a persistent store with run IDs and deduplication logic is essential.

3. **Decimal precision is fragile at the CSV boundary.** Amounts are parsed as `Decimal(row['amount_cents']) / 100`, which works for clean integer inputs but will silently mismatch if upstream systems send floats, localized number formats (e.g. `1.000,50`), or mixed currencies — causing legitimate matches to be classified as mismatches without any error raised.
```
