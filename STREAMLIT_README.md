# Reconciliation MVP - Streamlit App

Interactive web dashboard for reconciling platform transactions with bank entries.

## Features

- 📊 **Visual Dashboard** - Charts and metrics showing match rates and confidence distributions
- 📁 **CSV Upload** - Drag-and-drop interface for platform and bank data
- 🔍 **Detailed Views** - Browse matched and mismatched records with filtering
- 💾 **Export Results** - Download results as JSON or CSV
- ⚡ **Real-time Processing** - Instant reconciliation upon upload

## Installation

### Option 1: Using pip

```bash
# Navigate to project directory
cd /Users/jayvardhan.patil/Documents/jayshiai/leader

# Install Streamlit dependencies
pip install -r requirements-streamlit.txt

# Or install individually
pip install streamlit pandas plotly
```

### Option 2: Using virtual environment (recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-streamlit.txt
```

## Running the App

### Local Development

```bash
# From the project root directory
cd /Users/jayvardhan.patil/Documents/jayshiai/leader

# Run Streamlit
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

### Generate Sample Data

```bash
# Generate test data with gap scenarios
PYTHONPATH=/Users/jayvardhan.patil/Documents/jayshiai/leader:$PYTHONPATH python3 test_data_generator/generate.py

# Now upload these files in the Streamlit app:
# - test_data_generator/output/platform_transactions.csv
# - test_data_generator/output/bank_statement.csv
```

## Deployment Options

### 1. Streamlit Cloud (Free)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy!

Required files in repo root:
- `streamlit_app.py` (main app)
- `requirements-streamlit.txt` (dependencies)
- `recon/` package directory

### 2. Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-streamlit.txt .
RUN pip install -r requirements-streamlit.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t recon-app .
docker run -p 8501:8501 recon-app
```

### 3. Heroku

1. Create `Procfile`:
```
web: streamlit run streamlit_app.py --server.port=$PORT
```

2. Create `runtime.txt`:
```
python-3.11.x
```

3. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

### 4. AWS/GCP/Azure

Deploy the Docker container to:
- AWS ECS / EKS
- Google Cloud Run
- Azure Container Instances

## CSV Format Requirements

### Platform Transactions CSV

| Column | Type | Description |
|--------|------|-------------|
| platform_txn_id | string | Unique transaction ID |
| external_ref_id | string | Reference echoed by bank (nullable) |
| merchant_id | string | Merchant identifier |
| amount_cents | integer | Gross amount in cents |
| fee_cents | integer | Platform fee in cents |
| net_amount_cents | integer | Net amount (amount - fee) |
| status | string | Transaction status |
| initiated_at | ISO8601 | Timestamp when initiated |
| expected_settlement_date | date | Expected settlement date |
| payment_method | string | Payment method (card, etc.) |
| notes | string | Additional notes |

### Bank Statement CSV

| Column | Type | Description |
|--------|------|-------------|
| bank_ref_id | string | Unique bank entry ID |
| value_date | date | Value date (YYYY-MM-DD) |
| posting_date | date | Posting date (YYYY-MM-DD) |
| amount_cents | integer | Net amount in cents (can be negative) |
| description | string | Transaction description |
| counterparty_ref | string | Reference from platform (nullable) |
| notes | string | Additional notes |

## Screenshots

### Dashboard Overview
- Match confidence pie chart
- Match summary bar chart
- Key metrics cards

### Matches Tab
- Sortable table of all matched records
- Score progress bars
- Download as CSV

### Mismatches Tab
- Pie chart of mismatch types
- Detailed mismatch records
- Export functionality

### Export Tab
- Download full results as JSON
- Download summary as text
- Copy results to clipboard

## Troubleshooting

### Port already in use
```bash
# Kill process on port 8501
lsof -ti:8501 | xargs kill -9

# Or run on different port
streamlit run streamlit_app.py --server.port 8502
```

### Module not found errors
Make sure you're running from the project root:
```bash
cd /Users/jayvardhan.patil/Documents/jayshiai/leader
streamlit run streamlit_app.py
```

### CSV parsing errors
- Check CSV headers match expected format
- Ensure amount_cents are integers
- Verify dates are in ISO8601 format

## Development

### Hot Reload
Streamlit automatically reloads when you save changes to `streamlit_app.py`

### Adding New Features
1. Edit `streamlit_app.py`
2. Test locally with `streamlit run streamlit_app.py`
3. Commit and push changes

### Custom Styling
Modify the theme in `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main project README
3. Open an issue on GitHub

## License

Same as main project (see root LICENSE file)
