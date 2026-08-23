import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

#SEA_path = os.getcwd() + '/data/'
#SEA_path = "C:/Users/Alex/Documents/Research/InputOutput/data/"
path = Path("C:/Users/Alex/Documents/Research/political_economy_accounts/data/WIOT/")

def log1p(x):
    
    return np.log10(x+1)

def load_sea():
    
    # First, load parquet if exists - faster
    pq_fname = path / 'Socio_Economic_Accounts.parquet'
    if os.path.exists(pq_fname):
        SEA_df = pd.read_parquet(pq_fname)
     
    # If no parquet, then load as excel and save to parquet for next time.
    else:
        fname = path / 'Socio_Economic_Accounts.xlsx'
        SEA_df = pd.read_excel(fname, sheet_name='DATA')
        SEA_df.set_index(['country', 'variable', 'description', 'code'], inplace=True)
        SEA_df.columns = SEA_df.columns.astype(int)
        
        SEA_df.to_parquet(path / 'Scio_Economic_Accounts.parquet')
    
    # df.to_parquet(self.data_dir / 'lr_wiod_sea_final.parquet')
    return SEA_df

def load_exchange_rates():
    '''
    Ratio of US$ per Unit of Local Currency
    
    e = US$ / Nat Cur
    '''
    
    # Load parquet if exists - faster
    pq_fname = path / 'Exchange_Rates.parquet'
    if os.path.exists(pq_fname):
        EXR_df = pd.read_parquet(pq_fname)
        
    # Else if no parquet then load as excel and save to parquet for next time
    else:
        fname = path / 'Exchange_Rates.xlsx'
        EXR_df = pd.read_excel(fname, sheet_name='EXR', skiprows=3 ) # US Dollars per Unit of Local Currency
        EXR_df.rename(columns=lambda x: x.lstrip('_'), inplace=True) # Remove underlines in the beginning of each year
        EXR_df.drop(columns='Country', inplace=True)
        EXR_df.set_index(['Acronym'], inplace=True)
        EXR_df.columns = EXR_df.columns.astype(int)
    return EXR_df

'''
def load_niot(self, country):
    
    file = path / "NIOT" / f"{country}_NIOT_nov16.parquet"
    
    # Check if the parquet file does not exist
    # If does not exist, then create
    if not file.is_file():
        
        file = path / "NIOTS" / f"{country}_NIOT_nov16.xlsx"

        df = pd.read_excel(file, sheet_name="National IO-tables")

        df.set_index(["Year", "Code", "Description", "Origin"], inplace=True)

        df.columns = pd.MultiIndex.from_tuples(zip(df.columns, df.iloc[0]))
        df = df.iloc[1:]
        
        # Multi-index from tuples of y (year), c (code), d (desc), o (origin)
        df.index = pd.MultiIndex.from_tuples(
            [(int(y), c, d, o) for y, c, d, o in df.index],
            names=[x.lower() for x in df.index.names]
        )

        df = df.apply(pd.to_numeric)

        # Save to parquet for future use
        df.to_parquet(self.data_dir / "NIOTS" / f"{country}_NIOT_nov16.parquet")

    # Now that we confirm parquet file exists, load
    df = pd.read_parquet(file)
    
    return df
'''