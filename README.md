# One-Labs — Reconciliation MVP

A tool that matches platform transactions with bank statement entries to find exact, probable, and low-confidence matches.

## What it does

Upload a platform transactions CSV and a bank statement CSV. The engine matches them by reference ID, amount, and date, then tells you what matched, what didn't, and how confident it is.

## How to run

Install dependencies:
```
pip install -e ".[all]"
```

Generate test data:
```
bash generate_data.sh
```

Run from CLI:
```
python main.py --transactions platform.csv --bank-entries bank.csv --output result.json
```

Run the dashboard:
```
streamlit run streamlit_app.py
```

## Project structure

```
recon/          core matching logic
streamlit_app.py    web dashboard
main.py         CLI entry point
test_data_generator/    creates sample CSVs
tests/unit/     unit tests
```

## Requirements

Python 3.10+, streamlit, pandas, plotly

## Run tests

```
pytest
```

---

## ⚠️ Production Concerns

1. The in-memory repository will crash on large datasets — needs a database-backed storage layer.
2. There is no idempotency logic, so re-running the same files will create duplicate match records.
3. Amount parsing will silently fail on float inputs or localized number formats, causing real matches to be missed.
