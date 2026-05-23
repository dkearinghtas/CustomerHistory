import os
import pandas as pd
from pathlib import Path

class InvoiceDataLoader:
    """Loads and processes invoice data from CSV or live Azure SQL."""

    def __init__(self, csv_path=None, use_live=False, connection_string=None):
        self.csv_path = csv_path
        self.use_live = use_live
        self.connection_string = connection_string or os.getenv('FABRIC_SQL_CONNECTION')
        self.df = None
        self.load_data()

    def load_data(self):
        """Load data from live source or CSV and prepare for display"""
        if self.use_live:
            self.df = self.load_from_fabric()
        elif self.csv_path and Path(self.csv_path).is_file():
            self.df = pd.read_csv(self.csv_path)
            self.df.columns = self.df.columns.str.strip()
            self.df = self.df.rename(columns={
                'INVOICE_NUMBER.1': 'INVOICE_NUMBER',
                'INVOICE_DATE': 'HISTHDR.INVOICE_DATE',
                'LAST_NAME': 'HISTHDR.LAST_NAME'
            })
            if 'TIRE_SIZE' in self.df.columns and 'DESCRIPTION' in self.df.columns:
                self.df['TIRE_SIZE_STR'] = self.df['TIRE_SIZE'].astype(str).replace(['nan', 'None', 'NULL'], '')
                def prefix_description(row):
                    val = row['TIRE_SIZE_STR']
                    tire_size = str(val).strip() if pd.notna(val) else ""
                    desc = str(row['DESCRIPTION']).strip()
                    if tire_size and tire_size.lower() != 'nan':
                        return f"{tire_size} {desc}"
                    return desc
                self.df['DESCRIPTION'] = self.df.apply(prefix_description, axis=1)
            self.df = self.df[~self.df['ITEM_NUMBER'].astype(str).str.upper().eq('FET')]
            date_col = 'HISTHDR.INVOICE_DATE'
            if date_col in self.df.columns:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
            numeric_cols = ['QUANTITY', 'SELL_PRICE', 'SELL_LABOR']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        else:
            raise FileNotFoundError('No valid CSV path or live data connection available.')

    def load_from_fabric(self):
        """Load simplified data from Microsoft Fabric / Azure SQL via ODBC connection."""
        import pyodbc
        if not self.connection_string:
            raise ValueError('Connection string missing. Set FABRIC_SQL_CONNECTION env var.')

        query = """
            SELECT 
                l.INVOICE_NUMBER,
                h.INVOICE_DATE AS [HISTHDR.INVOICE_DATE],
                h.LAST_NAME AS [HISTHDR.LAST_NAME],
                l.ITEM_NUMBER,
                l.DESCRIPTION AS DESCRIPTION,
                l.QUANTITY,
                l.SELL_PRICE,
                l.SELL_LABOR,
                l.TIRE_SIZE AS TIRE_SIZE
            FROM HISTLINE l
            JOIN HISTHDR h ON l.INVOICE_NUMBER = h.INVOICE_NUMBER AND l.COMPANY = h.COMPANY
            WHERE l.ITEM_NUMBER != 'FET' AND h.INVOICE_DATE >= '2024-01-01' AND l.COMPANY = '1826'
        """

        conn = pyodbc.connect(self.connection_string)
        try:
            df = pd.read_sql(query, conn)
        finally:
            conn.close()

        if 'HISTHDR.INVOICE_DATE' in df.columns:
            df['HISTHDR.INVOICE_DATE'] = pd.to_datetime(df['HISTHDR.INVOICE_DATE'], errors='coerce')
        for col in ['QUANTITY', 'SELL_PRICE', 'SELL_LABOR']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_chronological_view(self):
        df_sorted = self.df.sort_values(
            'HISTHDR.INVOICE_DATE', 
            ascending=False, 
            na_position='last'
        )
        return df_sorted.copy()
    
    def get_parts_grouped_view(self, df):
        parts_df = df[df['SELL_PRICE'] > 0].copy()
        if len(parts_df) == 0:
            return pd.DataFrame()
        grouped = parts_df.groupby(['ITEM_NUMBER', 'DESCRIPTION']).agg({
            'INVOICE_NUMBER': 'count',
            'QUANTITY': 'sum',
            'SELL_PRICE': ['max', 'min', lambda x: x.mode().iloc[0] if not x.mode().empty else None],
            'HISTHDR.INVOICE_DATE': 'max'
        }).reset_index()
        grouped.columns = ['Item Number', 'Description', 'Purchase Count', 'Total Quantity', 
                          'Max Price', 'Min Price', 'Common Price', 'Most Recent Date']
        sorted_by_date = parts_df.sort_values('HISTHDR.INVOICE_DATE', ascending=False)
        recent_prices = sorted_by_date.groupby(['ITEM_NUMBER', 'DESCRIPTION'])['SELL_PRICE'].first().reset_index()
        recent_prices.columns = ['Item Number', 'Description', 'Most Recent Price']
        grouped = grouped.merge(recent_prices, on=['Item Number', 'Description'], how='left')
        return grouped.sort_values('Purchase Count', ascending=False)
    
    def get_labor_grouped_view(self, df):
        labor_df = df[df['SELL_LABOR'] > 0].copy()
        if len(labor_df) == 0:
            return pd.DataFrame()
        grouped = labor_df.groupby(['ITEM_NUMBER', 'DESCRIPTION']).agg({
            'INVOICE_NUMBER': 'count',
            'QUANTITY': 'sum',
            'SELL_LABOR': ['max', 'min', lambda x: x.mode().iloc[0] if not x.mode().empty else None],
            'HISTHDR.INVOICE_DATE': 'max'
        }).reset_index()
        grouped.columns = ['Item Number', 'Description', 'Labor Count', 'Total Quantity', 
                          'Max Labor', 'Min Labor', 'Common Labor', 'Most Recent Date']
        sorted_by_date = labor_df.sort_values('HISTHDR.INVOICE_DATE', ascending=False)
        recent_labor = sorted_by_date.groupby(['ITEM_NUMBER', 'DESCRIPTION'])['SELL_LABOR'].first().reset_index()
        recent_labor.columns = ['Item Number', 'Description', 'Most Recent Labor']
        grouped = grouped.merge(recent_labor, on=['Item Number', 'Description'], how='left')
        return grouped.sort_values('Labor Count', ascending=False)
    
    def get_unique_customers(self):
        col = 'HISTHDR.LAST_NAME'
        if col in self.df.columns:
            return sorted(self.df[col].dropna().astype(str).unique())
        return []
    
    def get_unique_invoice_numbers(self):
        if 'INVOICE_NUMBER' in self.df.columns:
            invoices = self.df['INVOICE_NUMBER'].dropna().unique()
            return sorted(str(inv) for inv in invoices)
        return []
    
    def get_unique_item_numbers(self):
        if 'ITEM_NUMBER' in self.df.columns:
            return sorted(self.df['ITEM_NUMBER'].dropna().astype(str).unique())
        return []
