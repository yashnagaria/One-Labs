#!/usr/bin/env python3
"""
Reconciliation Streamlit App
Interactive dashboard for reconciling platform transactions with bank entries.
"""

import csv
import json
from datetime import datetime
from decimal import Decimal
from io import StringIO

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from recon.domain.models import Transaction, BankEntry
from recon.usecases.reconcile import ReconcileUseCase
from recon.adapters.storage.in_memory_repo import InMemoryRepository


def load_platform_csv(uploaded_file):
    transactions = []
    content = uploaded_file.getvalue().decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    for row in reader:
        amount_dollars = Decimal(row['amount_cents']) / 100
        txn = Transaction(
            id=row['platform_txn_id'],
            reference_id=row['external_ref_id'] if row['external_ref_id'] else None,
            amount=amount_dollars,
            currency='USD',
            timestamp=datetime.fromisoformat(row['initiated_at']),
            metadata={
                'merchant_id': row.get('merchant_id', ''),
                'net_amount_cents': int(row.get('net_amount_cents', 0)),
                'fee_cents': int(row.get('fee_cents', 0)),
                'expected_settlement_date': row.get('expected_settlement_date', ''),
                'notes': row.get('notes', ''),
            }
        )
        transactions.append(txn)
    return transactions


def load_bank_csv(uploaded_file):
    entries = []
    content = uploaded_file.getvalue().decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    for row in reader:
        amount_dollars = Decimal(row['amount_cents']) / 100
        entry = BankEntry(
            id=row['bank_ref_id'],
            reference_id=row['counterparty_ref'] if row['counterparty_ref'] else None,
            amount=amount_dollars,
            currency='USD',
            timestamp=datetime.fromisoformat(row['value_date'] + 'T00:00:00'),
            metadata={
                'posting_date': row.get('posting_date', ''),
                'description': row.get('description', ''),
                'notes': row.get('notes', ''),
            }
        )
        entries.append(entry)
    return entries


def main():
    st.set_page_config(
        page_title="Reconciliation MVP",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 Reconciliation Dashboard")
    st.markdown("Match platform transactions with bank entries")
    
    with st.sidebar:
        st.header("📁 Data Upload")
        st.info("Upload your CSV files to begin reconciliation")
        
        platform_file = st.file_uploader(
            "Platform Transactions CSV",
            type=['csv'],
            help="CSV with columns: platform_txn_id, external_ref_id, merchant_id, amount_cents, fee_cents, net_amount_cents, status, initiated_at, expected_settlement_date, payment_method, notes"
        )
        
        bank_file = st.file_uploader(
            "Bank Statement CSV",
            type=['csv'],
            help="CSV with columns: bank_ref_id, value_date, posting_date, amount_cents, description, counterparty_ref, notes"
        )
        
        st.markdown("---")
        st.header("⚙️ Options")
        
        show_matched = st.checkbox("Show matched records", value=True)
        show_mismatched = st.checkbox("Show mismatched records", value=True)
        
        st.markdown("---")
        st.caption("Reconciliation MVP v0.1.0")
    
    if platform_file and bank_file:
        with st.spinner("Processing..."):
            transactions = load_platform_csv(platform_file)
            bank_entries = load_bank_csv(bank_file)
            
            repository = InMemoryRepository()
            use_case = ReconcileUseCase(repository=repository)
            result = use_case.execute(transactions, bank_entries)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Platform Transactions",
                result.stats['total_transactions']
            )
        
        with col2:
            st.metric(
                "Bank Entries",
                result.stats['total_bank_entries']
            )
        
        with col3:
            st.metric(
                "Matched",
                result.stats['total_matches'],
                delta=f"{result.stats['total_matches'] / result.stats['total_transactions'] * 100:.1f}%"
            )
        
        with col4:
            total_unmatched = result.stats['unmatched_transactions'] + result.stats['unmatched_bank_entries']
            st.metric(
                "Unmatched",
                total_unmatched,
                delta=f"{total_unmatched / (result.stats['total_transactions'] + result.stats['total_bank_entries']) * 100:.1f}%",
                delta_color="inverse"
            )
        
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "✅ Matches", "❌ Mismatches", "💾 Export"])
        
        with tab1:
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Match Confidence Distribution")
                
                confidence_data = {
                    'Category': ['Exact (≥0.9)', 'Probable (0.6-0.9)', 'Low Confidence (<0.6)'],
                    'Count': [
                        result.stats['exact_matches'],
                        result.stats['probable_matches'],
                        result.stats['low_confidence_matches']
                    ]
                }
                df_confidence = pd.DataFrame(confidence_data)
                
                fig = px.pie(
                    df_confidence,
                    values='Count',
                    names='Category',
                    color='Category',
                    color_discrete_map={
                        'Exact (≥0.9)': '#00CC96',
                        'Probable (0.6-0.9)': '#FFA15A',
                        'Low Confidence (<0.6)': '#EF553B'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            with col_right:
                st.subheader("Match Summary")
                
                match_data = {
                    'Type': ['Transactions Matched', 'Transactions Unmatched', 
                           'Bank Entries Matched', 'Bank Entries Unmatched'],
                    'Count': [
                        result.stats['total_matches'],
                        result.stats['unmatched_transactions'],
                        result.stats['total_matches'],
                        result.stats['unmatched_bank_entries']
                    ]
                }
                df_match = pd.DataFrame(match_data)
                
                fig = px.bar(
                    df_match,
                    x='Type',
                    y='Count',
                    color='Type',
                    color_discrete_sequence=['#636EFA', '#EF553B', '#636EFA', '#EF553B']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("Exact Matches", result.stats['exact_matches'])
            
            with col_stats2:
                st.metric("Probable Matches", result.stats['probable_matches'])
            
            with col_stats3:
                st.metric("Low Confidence", result.stats['low_confidence_matches'])
        
        with tab2:
            if show_matched and result.matches:
                st.subheader(f"Matched Records ({len(result.matches)})")
                
                matches_data = []
                for m in result.matches:
                    txn = next((t for t in transactions if t.id == m.transaction_id), None)
                    bank = next((b for b in bank_entries if b.id == m.bank_entry_id), None)
                    
                    matches_data.append({
                        'Transaction ID': m.transaction_id,
                        'Bank Entry ID': m.bank_entry_id,
                        'Reference': txn.reference_id if txn else '',
                        'Amount ($)': float(txn.amount) if txn else 0,
                        'Score': round(m.score, 3),
                        'Classification': m.classification.value,
                        'Matcher': m.matcher_used,
                        'Reason': m.reason
                    })
                
                df_matches = pd.DataFrame(matches_data)
                
                st.dataframe(
                    df_matches,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Amount ($)': st.column_config.NumberColumn(format="$%.2f"),
                        'Score': st.column_config.ProgressColumn(min_value=0, max_value=1)
                    }
                )
                
                st.download_button(
                    label="Download Matches as CSV",
                    data=df_matches.to_csv(index=False),
                    file_name="matches.csv",
                    mime="text/csv"
                )
            elif not show_matched:
                st.info("Showing matched records is disabled in sidebar")
            else:
                st.info("No matches found")
        
        with tab3:
            if show_mismatched and result.mismatches:
                st.subheader(f"Mismatched Records ({len(result.mismatches)})")
                
                mismatches_data = []
                for mm in result.mismatches:
                    mismatches_data.append({
                        'Type': mm.type.value.replace('_', ' ').title(),
                        'Transaction ID': mm.transaction_id or '-',
                        'Bank Entry ID': mm.bank_entry_id or '-',
                        'Details': mm.details
                    })
                
                df_mismatches = pd.DataFrame(mismatches_data)
                
                type_counts = df_mismatches['Type'].value_counts()
                col_pie, col_table = st.columns([1, 2])
                
                with col_pie:
                    fig = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="Mismatch Types"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_table:
                    st.dataframe(
                        df_mismatches,
                        use_container_width=True,
                        hide_index=True
                    )
                
                st.download_button(
                    label="Download Mismatches as CSV",
                    data=df_mismatches.to_csv(index=False),
                    file_name="mismatches.csv",
                    mime="text/csv"
                )
            elif not show_mismatched:
                st.info("Showing mismatched records is disabled in sidebar")
            else:
                st.success("🎉 No mismatches found! All records reconciled.")
        
        with tab4:
            st.subheader("Export Results")
            
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
            
            json_str = json.dumps(output_data, indent=2)
            
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                st.download_button(
                    label="📥 Download Full Results (JSON)",
                    data=json_str,
                    file_name="reconciliation_results.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col_dl2:
                summary_text = f"""
Reconciliation Summary
======================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Statistics:
- Platform Transactions: {result.stats['total_transactions']}
- Bank Entries: {result.stats['total_bank_entries']}
- Total Matches: {result.stats['total_matches']}
  * Exact: {result.stats['exact_matches']}
  * Probable: {result.stats['probable_matches']}
  * Low Confidence: {result.stats['low_confidence_matches']}
- Unmatched Transactions: {result.stats['unmatched_transactions']}
- Unmatched Bank Entries: {result.stats['unmatched_bank_entries']}

Match Rate: {result.stats['total_matches'] / result.stats['total_transactions'] * 100:.1f}%
"""
                st.download_button(
                    label="📄 Download Summary (TXT)",
                    data=summary_text,
                    file_name="reconciliation_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    else:
        st.info("👆 Please upload both CSV files to begin reconciliation")
        
        with st.expander("📖 Need sample data?"):
            st.markdown("""
            Generate sample test data using the test data generator:
            
            ```bash
            python test_data_generator/generate.py
            ```
            
            This will create:
            - `test_data_generator/output/platform_transactions.csv`
            - `test_data_generator/output/bank_statement.csv`
            
            Upload these files to see the reconciliation in action!
            """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sample Transactions", "~200")
        
        with col2:
            st.metric("Gap Scenarios", "4")
        
        with col3:
            st.metric("Expected Matches", "~185")


if __name__ == "__main__":
    main()
