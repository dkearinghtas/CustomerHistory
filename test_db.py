import os
from dotenv import load_dotenv
from data_loader import InvoiceDataLoader

def test():
    print("Loading environment variables...")
    load_dotenv()
    
    print("Testing connection to Azure SQL...")
    try:
        loader = InvoiceDataLoader(use_live=True)
        print("\nSuccess! Database initialized without loading all data.")
        print("Fetching top 5 rows from in-memory dataframe...")
        print(loader.df.head())

        print(f"\nTotal rows loaded into RAM: {len(loader.df)}")
    except Exception as e:
        print("\nError fetching data:")
        print(e)

if __name__ == '__main__':
    test()
