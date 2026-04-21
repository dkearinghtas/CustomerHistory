import os
import pandas as pd
from pathlib import Path

class InvoiceDataLoader:
    """Loads and processes invoice data from CSV or live Microsoft Fabric semantic model."""

    def __init__(self, csv_path=None, use_live=False, connection_string=None, table_name=None):
        self.csv_path = csv_path
        self.use_live = use_live
        self.connection_string = connection_string or os.getenv('FABRIC_SQL_CONNECTION')
        self.table_name = table_name or os.getenv('FABRIC_TABLE_NAME', 'invoices')
        self.df = None
        self.load_data()

    def load_data(self):
        """Load data from live source or CSV and prepare for display"""
        if self.use_live:
            self.df = self.load_from_fabric()
        elif self.csv_path and Path(self.csv_path).is_file():
            self.df = pd.read_csv(self.csv_path)
        else:
            raise FileNotFoundError('No valid CSV path or live data connection available.')

        # Normalize column names - handle both old and new formats
        self.df.columns = self.df.columns.str.strip()

        # Map actual column names to expected names
        column_mapping = {
            'INVOICE_NUMBER.1': 'INVOICE_NUMBER',
            'INVOICE_DATE': 'HISTHDR.INVOICE_DATE',
            'LAST_NAME': 'HISTHDR.LAST_NAME'
        }

        self.df = self.df.rename(columns=column_mapping)

        # Prepend TIRE_SIZE to DESCRIPTION if it applies
        if 'TIRE_SIZE' in self.df.columns and 'DESCRIPTION' in self.df.columns:
            # Convert TIRE_SIZE to string and handle NULLs
            self.df['TIRE_SIZE_STR'] = self.df['TIRE_SIZE'].astype(str).replace(['nan', 'None', 'NULL'], '')
            
            def prefix_description(row):
                val = row['TIRE_SIZE_STR']
                tire_size = str(val).strip() if pd.notna(val) else ""
                desc = str(row['DESCRIPTION']).strip()
                if tire_size and tire_size.lower() != 'nan':
                    return f"{tire_size} {desc}"
                return desc
            
            self.df['DESCRIPTION'] = self.df.apply(prefix_description, axis=1)

        # Exclude specified item codes (including FET)
        self.df = self.df[~self.df['ITEM_NUMBER'].astype(str).str.upper().eq('FET')]

        # Clean up data types
        date_col = 'HISTHDR.INVOICE_DATE'
        if date_col in self.df.columns:
            self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')

        numeric_cols = ['QUANTITY', 'SELL_PRICE', 'SELL_LABOR']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    def load_from_fabric(self):
        """Load data from Microsoft Fabric semantic model via ODBC/SQL connection."""
        try:
            import pyodbc
        except ImportError as exc:
            raise ImportError('pyodbc is required for live Fabric access. install with `pip install pyodbc`.') from exc

        if not self.connection_string:
            raise ValueError('Connection string missing. Set FABRIC_SQL_CONNECTION env var.')

        query = f"SELECT * FROM {self.table_name}"  # adjust columns in SQL if needed

        conn = pyodbc.connect(self.connection_string)
        try:
            df = pd.read_sql(query, conn)
        finally:
            conn.close()

        return df
    
    def get_chronological_view(self):
        """Get invoices sorted by date (newest first)"""
        df_sorted = self.df.sort_values(
            'HISTHDR.INVOICE_DATE', 
            ascending=False, 
            na_position='last'
        )
        
        return df_sorted[[
            'INVOICE_NUMBER',
            'HISTHDR.INVOICE_DATE',
            'HISTHDR.LAST_NAME',
            'ITEM_NUMBER',
            'DESCRIPTION',
            'QUANTITY',
            'SELL_PRICE',
            'SELL_LABOR'
        ]].copy()
    
    def get_grouped_view(self):
        """Get purchase counts by customer and product"""
        grouped = self.df.groupby(['HISTHDR.LAST_NAME', 'DESCRIPTION']).agg({
            'INVOICE_NUMBER': 'count',
            'QUANTITY': 'sum',
            'SELL_PRICE': 'sum',
            'SELL_LABOR': 'sum'
        }).reset_index()
        
        grouped.columns = ['Customer', 'Item Description', 'Purchase Count', 
                          'Total Quantity', 'Total Price', 'Total Labor']
        
        return grouped.sort_values('Purchase Count', ascending=False)
    
    def get_parts_grouped_view(self, df):
        """Get parts grouped by description with max and most recent price"""
        # Filter to rows with SELL_PRICE > 0
        parts_df = df[df['SELL_PRICE'] > 0].copy()
        
        if len(parts_df) == 0:
            return pd.DataFrame()
        
        # Group by item number + description and aggregate
        # Use lambda for mode to pick the most frequent price
        grouped = parts_df.groupby(['ITEM_NUMBER', 'DESCRIPTION']).agg({
            'INVOICE_NUMBER': 'count',
            'QUANTITY': 'sum',
            'SELL_PRICE': ['max', 'min', lambda x: x.mode().iloc[0] if not x.mode().empty else None],
            'HISTHDR.INVOICE_DATE': 'max'
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ['Item Number', 'Description', 'Purchase Count', 'Total Quantity', 
                          'Max Price', 'Min Price', 'Common Price', 'Most Recent Date']
        
        # Get the most recent price for each unique item (Number + Description)
        sorted_by_date = parts_df.sort_values('HISTHDR.INVOICE_DATE', ascending=False)
        recent_prices = sorted_by_date.groupby(['ITEM_NUMBER', 'DESCRIPTION'])['SELL_PRICE'].first().reset_index()
        recent_prices.columns = ['Item Number', 'Description', 'Most Recent Price']
        
        # Merge to add most recent price
        grouped = grouped.merge(recent_prices, on=['Item Number', 'Description'], how='left')
        
        return grouped.sort_values('Purchase Count', ascending=False)
    
    def get_labor_grouped_view(self, df):
        """Get labor grouped by description with max and most recent labor cost"""
        # Filter to rows with SELL_LABOR > 0
        labor_df = df[df['SELL_LABOR'] > 0].copy()
        
        if len(labor_df) == 0:
            return pd.DataFrame()
        
        # Group by item number + description and aggregate
        # Use lambda for mode to pick the most frequent labor cost
        grouped = labor_df.groupby(['ITEM_NUMBER', 'DESCRIPTION']).agg({
            'INVOICE_NUMBER': 'count',
            'QUANTITY': 'sum',
            'SELL_LABOR': ['max', 'min', lambda x: x.mode().iloc[0] if not x.mode().empty else None],
            'HISTHDR.INVOICE_DATE': 'max'
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ['Item Number', 'Description', 'Labor Count', 'Total Quantity', 
                          'Max Labor', 'Min Labor', 'Common Labor', 'Most Recent Date']
        
        # Get the most recent labor cost for each unique item (Number + Description)
        sorted_by_date = labor_df.sort_values('HISTHDR.INVOICE_DATE', ascending=False)
        recent_labor = sorted_by_date.groupby(['ITEM_NUMBER', 'DESCRIPTION'])['SELL_LABOR'].first().reset_index()
        recent_labor.columns = ['Item Number', 'Description', 'Most Recent Labor']
        
        # Merge to add most recent labor
        grouped = grouped.merge(recent_labor, on=['Item Number', 'Description'], how='left')
        
        return grouped.sort_values('Labor Count', ascending=False)
    
    def get_unique_customers(self):
        """Get list of unique customer names for dropdown"""
        customer_col = 'HISTHDR.LAST_NAME' if 'HISTHDR.LAST_NAME' in self.df.columns else 'LAST_NAME'
        if customer_col in self.df.columns:
            customers = self.df[customer_col].dropna().unique()
            return sorted(customers)
        return []
    
    def get_unique_invoice_numbers(self):
        """Get list of unique invoice numbers for dropdown"""
        if 'INVOICE_NUMBER' in self.df.columns:
            invoices = self.df['INVOICE_NUMBER'].dropna().unique()
            return sorted(str(inv) for inv in invoices)
        return []
    
    def get_unique_item_numbers(self):
        """Get list of unique item numbers for dropdown"""
        if 'ITEM_NUMBER' in self.df.columns:
            items = self.df['ITEM_NUMBER'].dropna().unique()
            return sorted(items)
        return []
