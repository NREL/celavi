import pandas as pd

class ReedsImporter:
    
    def __init__(self,
                 reeds_imported_filename,reeds_output_filename):
        
        self.reeds_imported_filename = reeds_imported_filename
        self.reeds_output_filename = reeds_output_filename
        
    def state_level_reeds_importer(self):
        
        
        df  = pd.read_csv(self.reeds_imported_filename)
        cols = df.columns
        cols = cols[2:]
        df2 = df.melt(id_vars = ['state','year'], value_vars = cols, value_name = 'value', var_name = 'product')
        
        year = [] 
        state = []
        states = pd.unique(df2['state'])
        flows = pd.unique(df2['product'])
        flow = []
        "Create the missing odd years"
        for fl in flows:
            for st in states:
                for y in range(2021,2050,2):
                    year.append(y)
                    state.append(st)
                    flow.append(fl)
        
        df4 = pd.DataFrame()
        df4['state'] = state
        df4['year'] = year
        df4['product'] = flow
             
        df5 = df2.merge(df4, on = ['state','year','product'], how = 'outer')   
        df6= df5.sort_values(by = ['product','state','year'])
        
        df7 = df6.interpolate(method = 'linear',limit_direction ='forward',limit = 1)
        
        df2 = df7
        df2['process'] = 'electricity'
        df2['unit'] = 'kWh'
        df2['stage'] = 'upstream'
        df2['source'] = 'REEDS'
        df2.loc[df2['product'] == 'electricity', 'input'] = 'FALSE'
        df2.loc[df2['product'] != 'electricity', 'input'] = 'TRUE'
        df2['location'] = 'US'
        df3 = df2[['state','process','product','location','unit','value','input','source','year','stage']]
        df3 = df3.sort_values(by = ['state','year'])
        
        df3.to_csv(self.reeds_output_filename,index = False)
        
        
    def national_level_reeds_importer(self):
            
            
            df  = pd.read_csv(self.reeds_imported_filename)
            cols = df.columns
            cols = cols[2:]
            df2 = df.melt(id_vars = ['year'], value_vars = cols, value_name = 'value', var_name = 'product')
            
            year = []
            flows = pd.unique(df2['product'])
            flow = []
            "Create the missing odd years"
            for fl in flows:
                    for y in range(2021,2050,2):
                        year.append(y)
                        flow.append(fl)
            
            df4 = pd.DataFrame()
            df4['year'] = year
            df4['product'] = flow
                 
            df5 = df2.merge(df4, on = ['year','product'], how = 'outer')   
            df6= df5.sort_values(by = ['product','year'])
            
            df7 = df6.interpolate(method = 'linear',limit_direction ='forward',limit = 1)
            
            df2 = df7
            df2['process'] = 'electricity'
            df2['unit'] = 'kWh'
            df2['stage'] = 'upstream'
            df2['source'] = 'REEDS'
            df2.loc[df2['product'] == 'electricity', 'input'] = 'FALSE'
            df2.loc[df2['product'] != 'electricity', 'input'] = 'TRUE'
            df2['location'] = 'US'
            df3 = df2[['process','product','location','unit','value','input','source','year','stage']]
            df3 = df3.sort_values(by = ['year'])
            
            df3.to_csv(self.reeds_output_filename,index = False)       
            