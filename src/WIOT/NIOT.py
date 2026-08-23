# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 19:53:08 2026

@author: Alex
"""
import os
from pathlib import Path
import pandas as pd
import loaders

from metadata.wiod_codes import WIOD_INDUSTRY_CODES

path = Path("C:/Users/Alex/Documents/Research/political_economy_accounts/data/WIOT/")
src_path = Path("C:/Users/Alex/Documents/Research/political_economy_accounts/src/WIOT/")


class NIOT:
    
    def __init__(self, name, sea, exr, * , sector_mapping=False, save_test_output=False, deflate=False):
        '''
        name - Three letter code for nation
        sea  - Dataframe of the scio-economic accounts for all nations
        exr  - Dataframe of the exchange rates for all nations
        '''
        
        self.name = name
        
        # --- Load Tables -----------------------------------------------------
        
        # Load the Socio-economic accounts
        # This data is in each nations local currency
        self.sea_raw = sea.loc[name]
        self.sea_raw.columns = self.sea_raw.columns.astype(int)
        
        # Grab any price indices (if needed)
        self.go_pi = self.sea_raw.loc['GO_PI'].reorder_levels(['code', 'description']) / 100.
        self.ii_pi = self.sea_raw.loc['II_PI'].reorder_levels(['code', 'description']) / 100.
        self.va_pi = self.sea_raw.loc['VA_PI'].reorder_levels(['code', 'description']) / 100.
                
        # Load the Exchange rates
        # This is the ratio between the US$ to the Local Currency
        # e = US$ / Local Curr
        #
        # So :
        #      e * Local Curr = US$
        # or    
        #      US$ / e = Local Curr
        #
        # Note that Romania (ROU) is the one nation where there is a mismatch in names in the datasets
        # In the NIOT and SEA it is ROU
        # In the EXR file, though, it is ROM
        if self.name == 'ROU':
            self.exr = exr.loc['ROM']
        else:
            self.exr = exr.loc[name]
        self.exr.index = self.exr.index.astype(int)
        
        # Load the National Input Output Table
        # This data is in millions of US$
        self.niot_raw = self.load_niot(name) * 1e6 # Turn denoted millions US$ into just US$
        
        # Define sector codes from metadata folder
        self.codes = WIOD_INDUSTRY_CODES
        
        # -- Deflate ----------------------------------------------------------
        # Because aggregation occurs before pulling distinct variables,
        # We must also deflate before pulling variables 
        # Why? Well I'm not sure how to meaningfully construct an aggregated price index - I have ideas... but it may be safer
        #     to defalate the raw data and THEN aggregate, even if that is more annoying to do...
        
        # There are three price indices
        # A gross output price index
        # An intermediate inputs price index
        # and a value adeed price index
        # Use the appropriate price index for each variable (or what I believe to be the appropriate price index...?)
        
        ### Deflate the Socio-Economic Accounts ###
        if deflate:
            # Deflate the gross output by the gross output price index
            self.sea_raw.loc['GO',:] = self.sea_raw.loc['GO'] / self.go_pi
            
            # Deflate the value added, and other incomes, by the value added price index
            self.sea_raw.loc['VA',:]   = self.sea_raw.loc['VA'] / self.va_pi
            self.sea_raw.loc['CAP',:]  = self.sea_raw.loc['CAP'] / self.va_pi 
            self.sea_raw.loc['COMP',:] = self.sea_raw.loc['COMP'] / self.va_pi 
            self.sea_raw.loc['LAB', :] = self.sea_raw.loc['LAB'] / self.va_pi 
            
            # Deflate the intermediate inputs by the intermediate inputs price index
            self.sea_raw.loc['II',:] = self.sea_raw.loc['II'] / self.ii_pi 
    
            # Deflate the capital stock. By what?
            # Let's assume the gros output
            self.sea_raw.loc['K', :] = self.sea_raw.loc['K'] / self.go_pi 
            
            ### Deflate the National Input Output Tables ###
            # (need to figure this one out...)
        
        
        # --- Aggregation -----------------------------------------------------
        # Aggregate if a sector mapping csv is given
        if sector_mapping:
            
            # Maybe make this schema_file variable the same as the sector_mapping
            # If False then no agg, else it should be the name of the file
            schema_file = 'mapping_schema_02.csv'

            # Add: Check if schema file exists
            mapping_df = pd.read_csv(src_path / 'metadata' / schema_file)
            
            # Aggregate the Socio-Economic Accounts
            sea_raw = self.aggregate_sea(self.sea_raw, mapping_df)
            self.sea_raw = sea_raw
            
            # Aggregate the National Input Output Tables
            niot_raw = self.aggregate_niot(self.niot_raw, mapping_df)
            self.niot_raw = niot_raw
            
            # Redefine sector codes from mapping/aggregation
            # Using pd.unique(), new codes appear in order of first appearance
            self.codes = mapping_df['mapped code'].unique().tolist()
        
        # --- Pull Distinct Variables -----------------------------------------
        # We now have a choice:
        # 1.) Do we use the local currency (in which case we must convert the NIOT table)
        # 2.) Or we do use US currency for all (in which case we convert the SEA to US$)
        # 3.) Other options would be using Purchasing Power Parity, some other common metric
        #
        # Let's go with opiton 2.) - Use US currency for all data
        # In the prepare_accounts() function (which uses the SEA) we will multiply the local currencies by the exchange rate to get US$
        
        # - Prepare Variables - #
        self._prepare_accounts(self.sea_raw) # Creates go, va, ii, emp, empe, lab, cap, K, years
        
        # - Prepare IO Tables - #
        self._preapre_input_output_tables(self.niot_raw, self.go, save_test_output=save_test_output)
        

    
    # ---------- Social Economic Accounts ----------
    
    def aggregate_sea(self, sea_df, mapping_df):
    
        
        
        # Create mappings from the original codes and descriptions to the new values
        code_mapping = mapping_df.set_index('code')['mapped code'].to_dict()
        description_mapping = mapping_df.set_index('description')['mapped description'].to_dict()
        
        # Grab the social economic account
        sea_raw = sea_df.copy()
        
        # Replace the MultiIndex levels
        sea_raw.index = pd.MultiIndex.from_arrays(
            [
                 sea_raw.index.get_level_values('variable'),
                 sea_raw.index.get_level_values('description').map(description_mapping),
                 sea_raw.index.get_level_values('code').map(code_mapping)
            ],
            names=sea_raw.index.names
        )
        
        # The sea_raw dataframe has now been updated with the new descriptions and codes
        # But it has not been aggregated
        
        # Aggregate the new codes/descriptions of the sea_raw
        
        # These variables will be summed.
        sum_variables = [
            'GO',
            'II',
            'VA',
            'EMP',
            'EMPE',
            'H_EMPE',
            'COMP',
            'LAB',
            'CAP',
            'K'
        ]
        
        # These variables are price or volume indices and I need to figure how how to aggregte them later
        index_variables = [
            'GO_PI', 'II_PI', 'VA_PI',
            'GO_QI', 'II_QI', 'VA_QI'
        ]
        
        sea_sum = (
            sea_raw.loc[sea_raw.index.get_level_values('variable').isin(sum_variables)]
            .groupby(level=['variable','description','code'])
            .sum()
        )
        
        # Figure out how to aggregate indices 
    
        return sea_sum

    def _prepare_accounts(self, sea_df):

        df = sea_df

        self.go = (df.loc["GO"] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        self.ii = (df.loc["II"] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        self.va = (df.loc["VA"] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        

        #Number of persons engaged (thousands)
        self.emp = (df.loc["EMP"] * 1e3).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        
        # Number of employees (thousands)
        self.empe = (df.loc['EMPE'] * 1e3).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        
        #Total hours worked by employees (millions) 
        self.h_empe = (df.loc['H_EMPE'] * 1e6).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        
        # Compensation of employees (millions of national currency)
        self.comp = (df.loc["COMP"] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        
        # Labour compensation (millions of national currency)
        self.lab = (df.loc['LAB'] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        
        # Capital compensation (in national currency)
        self.cap = (df.loc['CAP'] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)
        
        # Nominal capital stock (in millions of national currency)
        self.K = (df.loc['K'] * 1e6 * self.exr).reorder_levels(['code', 'description'])#.sort_index().sort_index(axis=1)

        # Price Indices
        # Fill out 'GO_PI', 'II_PI', 'VA_PI'
        
        # Volume Indices
        # Fill out 'GO_QI', 'II_QI', 'VA_QI'
        
        # Years
        self.years = list(self.go.columns)
        
        
    # ----------- National Input Output Tables ----------
    
    # ---- Load the National Input Output Table -----#
    def load_niot(self, country):
        '''
        
        Load the National Input Output DataFrame for a given Country
        
        Each country's Input Output data is in millions of US dollars

        Parameters
        ----------
        country : str
            Three letter description of the country

        Returns
        -------
        df : pd.DataFrame
            The National Input Output Table

        '''
        
        parquet_file = path / "NIOTS" / f"{country}_NIOT_nov16.parquet"
        
        # Check if the parquet file does not exist
        # If does not exist, then create
        if not parquet_file.is_file():
            
            excel_file = path / "NIOTS" / f"{country}_NIOT_nov16.xlsx"
    
            df = pd.read_excel(excel_file, sheet_name="National IO-tables")
    
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
            df.to_parquet(parquet_file)
    
        # Now that we confirm parquet file exists, load
        df = pd.read_parquet(parquet_file)
        
        return df
    
    
    def aggregate_niot(self, niot_df, mapping_df):
    
        # Mapping and Aggregating NIOT
        niot_raw = niot_df.copy()
        
        # Codes that should NOT be mapped
        niot_unmapped_codes = [
            'II_fob',
            'TXSP',
            'EXP_adj',
            'PURR',
            'PURNR',
            'VA',
            'IntTTM',
            'GO'
        ]
        
        # Create dictionaries from mapping_df
        code_mapping = mapping_df.set_index('code')['mapped code'].to_dict()
        description_mapping = mapping_df.set_index('code')['mapped description'].to_dict()
        
        ### Rows ###
        
        # Extract the existing row MultiIndex levels
        year = niot_raw.index.get_level_values('year')
        code = niot_raw.index.get_level_values('code')
        #description = niot_raw.index.get_level_values('description')
        origin = niot_raw.index.get_level_values('origin')
        
         # Map code and description, but leave unmapped NIOT codes untouched
        new_code = code.map(
            lambda x: x if x in niot_unmapped_codes else code_mapping.get(x, x)
        )
        
        # Can use codes to map new descriptions
        new_description = code.map(
            lambda x: x if x in niot_unmapped_codes else description_mapping.get(x, x)
        )
           
        # Reconstruct the row MultiIndex
        niot_raw.index = pd.MultiIndex.from_arrays(
            [
                year,
                new_code,
                new_description,
                origin
            ],
            names=['year', 'code', 'description', 'origin']
        )
        
        ### Columns ###
        
        # The columns which do not need to be re-mapped
        niot_unmapped_column_codes = [
            'CONS_h',
            'CONS_np',
            'CONS_g',
            'GFCF',
            'INVEN',
            'EXP',
            'GO'
        ]
        
        # Extract existing column MultiIndex levels
        column_code = niot_raw.columns.get_level_values(0)
        #column_description = niot_raw.columns.get_level_values(1) # only needs code
        
        # Map the columns, preserving the special NIOT columns
        new_column_code = column_code.map(
            lambda x: x if x in niot_unmapped_column_codes else code_mapping.get(x, x)
        )
        
        new_column_description = column_code.map(
            lambda x: x if x in niot_unmapped_column_codes else description_mapping.get(x, x)
        )
        
        # Reconstruct the column MultiIndex
        niot_raw.columns = pd.MultiIndex.from_arrays(
            [
                new_column_code,
                new_column_description
            ],
            names=niot_raw.columns.names
        )
        
        '''
        # Save so I can look at it
        path = Path("C:/Users/Alex/Documents/Research/political_economy_accounts/data/WIOT/")
        
        temp_output_path = path / 'temp_outputs'
        temp_output_path.mkdir(parents=True, exist_ok=True)
        
        print(f'Saving temporary file for input-output table to {temp_output_path}')
        
        niot_raw.to_csv(temp_output_path / f'niot_raw_remapped_{self.name}.csv')
        '''
        
        # Now aggregate the codes/descriptions
        # Aggregate rows
        niot_raw = (
            niot_raw
            .groupby(
                level=['year', 'code', 'description', 'origin'],
                sort=False
            )
            .sum()
        )
        
        # Aggregate columns
        niot_raw = (
            niot_raw.T
            .groupby(
                level=[0, 1],
                sort=False
            )
            .sum()
            .T
        )
        
        return niot_raw
    
    def _extract_domestic_io(self, df):
        return df.loc[:, :, :, "Domestic"][self.codes]


    def _extract_import_io(self, df):
        return df.loc[:, :, :, "Imports"][self.codes]
    
    def _compute_A(self, Z, gross_output):
        """
        Compute technical coefficients matrix A for all years.
        """
    
        A = Z.copy()
    
        for year in Z.index.levels[0]:
            Z_year = Z.loc[year]
            x = gross_output[year]# .swaplevel() # <---- if we swap the indiex levles of go at the start, then don't need this here.
    
            A.loc[year] = Z_year.div(x, axis=1).values
    
        return A.fillna(0)
    
    def _get_national_accounts(self, origin, variables):
        return (
            self.niot_raw
            .loc[:, self.codes, :, origin]
            .sort_index()
            [variables]
            .droplevel('origin')
            .unstack('year')
            .droplevel(level=1, axis=1) # Remove description and keep the code (which is simpler)
            .reorder_levels(['code', 'description']) # Ensure matches the order of SEA
        )
    
    def _preapre_input_output_tables(self, niot_df, gross_output, *, save_test_output=False):
        
        # Extract the domestic input output table from the national input outputs raw dataframe
        Z_dom = self._extract_domestic_io(niot_df)
        
        # Extra the imported input output table
        Z_imp = self._extract_import_io(niot_df)
        
        # Compute the techincal coefficients matrix (A) for all years...
        # ... for domestic input-outputs...
        A_dom = self._compute_A(Z_dom, gross_output)
        
        #... and for imported input-outputs...
        A_imp = self._compute_A(Z_imp, gross_output)
        
        # Assign as attributes
        self.Z_dom = Z_dom 
        self.Z_imp = Z_imp
        
        self.A_dom = A_dom
        self.A_imp = A_imp
        
        if save_test_output:
            temp_output_path = path / 'temp_outputs'
            temp_output_path.mkdir(parents=True, exist_ok=True)
            
            print(f'Saving temporary file for input-output table to {temp_output_path}')
            
            Z_dom.to_csv(temp_output_path / f'Z_dom_{self.name}.csv')
            A_dom.to_csv(temp_output_path / f'A_dom_{self.name}.csv')
            
        # --------------------------------------------------------------------#
        ## Domestic values ##
        ## Grab consumption, GFCF, inventories
        net_product_dom = self._get_national_accounts(
            'Domestic',
            ['CONS_h', 'CONS_np', 'CONS_g', 'GFCF', 'INVEN']
        )
        
        self.net_product_dom = net_product_dom
        

        # Grab just the consumption
        self.consumption_dom = net_product_dom[
            ['CONS_h', 'CONS_np', 'CONS_g']
        ]
        
        # Make dataframes for each consumption type
        self.cons_h_dom = net_product_dom['CONS_h']
        self.cons_np_dom = net_product_dom['CONS_np']
        self.cons_g_dom = net_product_dom['CONS_g']
        
        # Make dataframe for gross fixed capital formation and for change in inventories
        self.gfcf_dom = net_product_dom['GFCF']
        self.inven_dom = net_product_dom['INVEN']
        
        ## Imported Values ##
        ## Grab consumption, GFCF, inventories -- imports
        net_product_imp = self._get_national_accounts(
            'Imports',
            ['CONS_h', 'CONS_np', 'CONS_g', 'GFCF', 'INVEN']
        )
        
        self.net_product_imp = net_product_imp
        
        # Grab just the consumption
        self.consumption_imp = net_product_imp[
            ['CONS_h', 'CONS_np', 'CONS_g']
        ]
        
        # Make dataframes for each consumption type
        self.cons_h_imp = net_product_imp['CONS_h']
        self.cons_np_imp = net_product_imp['CONS_np']
        self.cons_g_imp = net_product_imp['CONS_g']
        
        # Make dataframe for gross fixed capital formation and for change in inventories
        self.gfcf_imp = net_product_imp['GFCF']
        self.inven_imp = net_product_imp['INVEN']
        
        ## Grab Exports and Gross Output
        
        # Grab exports
        self.exports = self._get_national_accounts(
            'Domestic',
            ['EXP']
        )['EXP']
                
        self.go_alt = self._get_national_accounts(
            'Domestic',
            ['GO']
        )['GO']
        
        
                   
        '''
        ## Grab net product composed of consumption, GFCF, change in inventories
        net_product_dom = self.niot_raw.loc[:, self.codes, :, 'Domestic'].sort_index()[[
            'CONS_h', 'CONS_np', 'CONS_g', 'GFCF', 'INVEN'
            ]].droplevel('origin' # Drop the origin multi-level
                         ).unstack('year' # Turn the year multi-level into a column
                                   ).droplevel(level=0, axis=1) # Remove the redundant extra column multi-level
        self.net_product_dom = net_product_dom 
        
        # Grab just the consumption
        consumption_dom = net_product_dom[['CONS_h', 'CONS_np', 'CONS_g']]
        self.consumption_dom = consumption_dom
        
        # Make dataframes for each consumption type
        cons_h_dom = consumption_dom['CONS_h']
        self.cons_h_dom = cons_h_dom
        
        cons_np_dom = consumption_dom['CONS_np']
        self.cons_np_dom = cons_np_dom
        
        cons_g_dom = consumption_dom['CONS_g']
        self.cons_g_dom = cons_g_dom 
        
        # Make dataframe for gross fixed capital formation
        gfcf_dom = net_product_dom['GFCF']
        self.gfcf_dom = gfcf_dom
        
        # Make dataframe for change in inventories
        inven_dom = net_product_dom['INVEN']
        self.inven_dom = inven_dom
        
        
        
        
        ## Grab Exports
        exports =  self.niot_raw.loc[:, self.codes, :, 'Domestic'].sort_index()[['EXP']].droplevel('origin' # Drop the origin multi-level
                     ).unstack('year' # Turn the year multi-level into a column
                               ).droplevel(level=0, axis=1) # Remove the redundant extra column multi-level
        self.exports = exports['EXP']
        
        ## Grab Gross Output (alt)
        gross_output_alt = self.niot_raw.loc[:, self.codes, :, 'Domestic'].sort_index()[['GO']].droplevel('origin' # Drop the origin multi-level
                     ).unstack('year' # Turn the year multi-level into a column
                               ).droplevel(level=0, axis=1)
        self.go_alt = gross_output_alt['GO']
        '''
            
        
        
        
        
        
        
