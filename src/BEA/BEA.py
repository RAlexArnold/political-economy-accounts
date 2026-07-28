import pandas as pd
import numpy as np

path = "C:/Users/Alex/Documents/Research/political_economy_accounts/"

def load_national_accounts_template(fname, subfolder='national_accounts', yearmin=1998, yearmax=2024):

    fpath = path + f'data/BEA/{subfolder}/'
    file_path = fpath + fname

    #if not (yearmin <= int(year) <= yearmax):
    #    raise ValueError("Year out of bounds")

    table_df = pd.read_csv(
        file_path,
        header=None,
        skipinitialspace=True,
        skiprows=3
    )

    # ---- Columns: years ----
    years = table_df.iloc[0, 2:].astype(int)

    # ---- Index: item names ----
    item_names = table_df.iloc[1:, 1].str.strip()

    # ---- Data ----
    data = table_df.iloc[1:, 2:]
    data = data.apply(pd.to_numeric, errors="coerce")

    # ---- Construct DataFrame ----
    df = pd.DataFrame(
        data.values,
        index=item_names,
        columns=years
    )

    # ---- Drop footnotes / empty rows ----
    df = df.loc[df.index.notna()]

    return df

class BEA():
    
    def __init__(self):
        
        #########################################################################
        ### These fields are not year-specific. All years are loaded together ###
        #########################################################################
        
        # Load the Gross Output
        go = self.load_go_table()
        self.go_all = go
        
        # Load the Hours Worked
        hours = self.load_hours_table()
        self.hours_all = hours
    
        """
        self.year = year

        io_df = self.load_IO_table(year)

        # Grab the A matrix, and per-output coefficients for used, other, employee comp, taxes, and operating surplus
        A, (used_coef, other_coef, comp_empe_coef, taxes_coef, comp_surp_coef) = self.construct_A_matrix(io_df)
        self.A = A
        
        self.industry_codes = A.index.get_level_values('item_code')
        self.industry_names = A.index.get_level_values('item_name')
        
        #gross_output_table = self.load_go_table(year)
        # Grab this year's gross output
        #self.gross_output = gross_output_table.loc[gross_output_table.index.get_level_values('sector_name').isin(self.industry_names), year].iloc[:,0]
        
        ###########################################################
        ## National Accounts
        ###########################################################
        '''
        comp_empe_df = load_national_accounts_template(self, year, 'Compensation of Employees by Industry 1998-2024.csv', yearmin=1998, yearmax=2024)
        FTPT_empe    = load_national_accounts_template(self, year, 'Full-Time and Part-Time Employees by Industry 1998-2024.csv')
        FTE_empe     = load_national_accounts_template(self, year, 'Full-Time Equivalent Employees by Industry 1998-2024.csv')
        wages_empe   = load_national_accounts_template(self, year, 'Wages and Salaries by Industry 1998-2024.csv')
        wages_FTE_empe = load_national_accounts_template(self, year, 'Wages and Salaries Per Full-Time Equivalent Employee by Industry 1998-2024.csv')

        personal_income = load_national_accounts_template(self, year, 'Personal Income and Its Disposition 1929-2024.csv', yearmin=1929, yearmax=2024)
        '''
        """
        
    def load_go_table(self):

        fpath = path + 'data/BEA/gross_output/'


        # Gross Output in Billions
        # https://apps.bea.gov/iTable/?reqid=1603&step=2&Categories=GDPxInd&isURI=1&_gl=1*1qcsk3*_ga*MTM5MTA0NTk4LjE3NjI5MDY1OTI.*_ga_J4698JNNFT*czE3NjcxMzQ1OTckbzUkZzEkdDE3NjcxMzYzODgkajUwJGwwJGgw#eyJhcHBpZCI6MTYwMywic3RlcHMiOlsxLDIsNCw0XSwiZGF0YSI6W1siY2F0ZWdvcmllcyIsIkdEUHhJbmQiXSxbIlRhYmxlX0xpc3QiLCJUR08xMDUiXSxbIlNjYWxlIiwiLTkiXSxbIkZpcnN0X1llYXIiLCIxOTk3Il0sWyJMYXN0X1llYXIiLCIyMDA0Il0sWyJSb3dzIixbIjIyUiJdXSxbIlNlcmllcyIsIkEiXSxbIkNvbHVtbnMiLFsiMjAyMCJdXV19
        
        fname = 'gross_output_by_industry_1997-2024.csv'

        file_path = fpath + fname

        table_df = pd.read_csv(
            file_path,
            header=None,
            skipinitialspace=True,
            skiprows=0
        )

        # Grab the Index Headers
        col_codes = table_df.iloc[0, 1:].astype(int)


        #columns = pd.MultiIndex.from_arrays(
        #    [col_codes],
        #    names=["year"]
        #)
        
        columns = pd.Index(
            col_codes,
            name='year'
            )

        #row_codes = table_df.iloc[1:, 0].str.strip()
        row_descs = table_df.iloc[1:, 0].str.strip()

        #index = pd.MultiIndex.from_arrays(
        #    [row_codes, row_descs],
        #    names=["item_code", "sector_name"]
        #)
        
        #index = pd.MultiIndex.from_arrays(
        #    #[row_codes, row_descs],
        #    [row_descs],
        #    #names=["item_code", "item_name"]
        #    names=['sector_name']
        #)
        
        index = pd.Index(
                row_descs,
                name='sector_name'
                )

        # Grab the Data
        data = table_df.iloc[1:, 1:].astype(float) * 1e9 # in billions


        # Create the table
        go_df = pd.DataFrame(
            data.values,
            index=index,
            columns=columns
        )

        # Remove the footnotes (NAN)
        go_df = go_df.loc[go_df.index.get_level_values(0).notna()]# & go_df.index.get_level_values(1).notna()]
        
        return go_df
        

            
    def load_hours_table(self):

        fpath = path + 'data/BEA/national_accounts/'

            
        # Hours in millions

        fname = 'Hours Worked by Full-Time and Part-Time Employees by Industry 2000-2022.csv'

        file_path = fpath + fname

        table_df = pd.read_csv(
            file_path,
            header=None,
            skipinitialspace=True,
            skiprows=0
        )

        # Grab the Index Headers
        col_codes = table_df.iloc[0, 1:].astype(int)


        #columns = pd.MultiIndex.from_arrays(
        #    [col_codes],
        #    names=["year"]
        #)
        
        columns = pd.Index(
            col_codes,
            name = 'year'
            )

        #row_codes = table_df.iloc[1:, 0].str.strip()
        row_descs = table_df.iloc[1:, 0].str.strip()

        #index = pd.MultiIndex.from_arrays(
        #    [row_codes, row_descs],
        #    names=["item_code", "sector_name"]
        #)
        
        #index = pd.MultiIndex.from_arrays(
        #    #[row_codes, row_descs],
        #    [row_descs],
        #    #names=["item_code", "item_name"]
        #    names=['sector_name']
        #)
        
        index = pd.Index(
            row_descs,
            name = 'sector_name'
            )

        # Grab the Data
        data = table_df.iloc[1:, 1:].astype(float) * 1e6 # in millions


        # Create the table
        L_df = pd.DataFrame(
            data.values,
            index=index,
            columns=columns
        )

        # Remove the footnotes (NAN)
        L_df = L_df.loc[L_df.index.get_level_values(0).notna()]# & go_df.index.get_level_values(1).notna()]
        
        return L_df   

        
    ### Year Specific ###
        
        
    def start(self, year):
        
        dom_io_df = self.load_domestic_IO_table(year)
        
        # Grab the A matrix, and per-output coefficients for used, other, employee comp, taxes, and operating surplus
        A, (used_coef, other_coef, comp_empe_coef, taxes_coef, comp_surp_coef) = self.construct_A_matrix(dom_io_df)
        self.A_df = A
        
        # Grab the year's data from the gross output and hours worked
        self.go_df = self.go_all[[year]]
        self.hours_df = self.hours_all[[year]]
        
        ## Construct the l vector
        l = self.construct_l_vector(self.hours_df, self.go_df)
        self.l_df = l
        
        ## Construct the v vector
        v = self.construct_v_vector(A,l)
        self.v_df = v

    def construct_l_vector(self, hours_df, go_df):

        # Calculate the (monetary) direct labor coefficients (unadjusted for productive vs unproductive)
        # The monetary direct labor coefficinets are the physical direct labor coefficients divded by the long-term (natural) price
        # $l = hours / $go
        # $l = L / (pq)   [direct labor per dollar of output]
        # $l = l / p
        l_df = hours_df/go_df
        
        return l_df


    def construct_v_vector(self, A_df, l_df):
                
        ### Calculate (monetary) labor-values ###
        
        # Grab the numpy versions
        l = l_df.to_numpy().T # make row vector
        A = A_df.to_numpy()
        
        I = np.eye(len(A))
        leon = np.linalg.inv(I - A)
        
        v = l @ leon
        
        # Turn value back into a pandas dataframe
        v_df = pd.DataFrame(v.T, index=l_df.index, columns=l_df.columns)
        
        return v_df
        

    def load_domestic_IO_table(self, year):

        fpath = path + 'data/BEA/IO_table/Direct Domestic Requirements, After Redefinitions - Sector/'
        fname = f'{year}_dom_IO.csv'
        file_path = fpath + fname

        table_df = pd.read_csv(
            file_path,
            header=None,
            skipinitialspace=True,
            skiprows=2
        )

        # Grab the Index Headers
        col_codes = table_df.iloc[0, 2:].str.strip()
        col_descs = table_df.iloc[1, 2:].str.strip()

        columns = pd.MultiIndex.from_arrays(
            [col_codes, col_descs],
            names=["sector_code", "sector_name"]
        )

        row_codes = table_df.iloc[2:, 0].str.strip()
        row_descs = table_df.iloc[2:, 1].str.strip()

        index = pd.MultiIndex.from_arrays(
            [row_codes, row_descs],
            names=["item_code", "item_name"]
        )

        # Grab the Data
        data = table_df.iloc[2:, 2:].astype(float)

        # Create the table
        io_df = pd.DataFrame(
            data.values,
            index=index,
            columns=columns
        )

        # Remove the footnotes (NAN)
        io_df = io_df.loc[io_df.index.get_level_values(0).notna() & io_df.index.get_level_values(1).notna()]


        return io_df


    def construct_A_matrix(self, io_df):

        # The Sectoral A matrix
        A = io_df.loc[
            io_df.index.get_level_values(0).isin(io_df.columns.get_level_values(0))
        ]

        # These are per-dollar-output coefficients
        used      = io_df.loc[('Used', 'Scrap, used and secondhand goods')]
        other     = io_df.loc[('Other', 'Noncomparable imports and rest-of-the-world adjustment')]
        comp_empe = io_df.loc[('V001', 'Compensation of employees')]
        taxes     = io_df.loc[('V002', 'Taxes on production and imports, less subsidies')]
        comp_surp = io_df.loc[('V003', 'Gross operating surplus')]

        return A, (used, other, comp_empe, taxes, comp_surp)

        
        


