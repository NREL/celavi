import pandas as pd


def postprocessing(final_res, insitu, verbose):
    """
    Combines the insitu and background pollutant flows.

    Parameters
    ----------
    final_res: pandas.DataFrame
       Background pollutant flow quantities.
    insitu: pandas.DataFrame
        Insitu pollutant flow quantities.
    verbose: int
        Controls the level of progress reporting from this method.
    
    Returns
    -------
    pandas.DataFrame
        Total pollutant flows for a material being processed through a facility.
        Columns:
            - flow name: str
                Pollutant name.
            - flow unit: str
                Unit of pollutant flow.
            - year: int
                Model year.
            - facility_id: int
                Facility ID.
            - stage: str
                Supply chain stage.
            - material: str
                Name of material.
            - route_id: str
                UUID of transportation route.
            - state: str
                State in which facility is located.
            - flow quantity: float
                Pollutant quantity.
    """
    if final_res.empty:
        if verbose == 1:
            print('pylca_celavi_background_postprocess: final_res is empty')
    else:
        pass
    
    if insitu.empty == False:
        # Adding up the insitu emission primarily for the cement manufacturing process
        final_res['flow name'] = final_res['flow name'].str.lower()
        
        column_names = ['flow name', 'flow unit', 'year', 'facility_id', 'stage', 'material', 'route_id','state']
        total_em = insitu.merge(final_res, on=column_names, how='outer')
        total_em = total_em.fillna(0)
        total_em['flow quantity'] = total_em['flow quantity_x'] + total_em['flow quantity_y']
        final_res = total_em.drop(columns = ['flow quantity_x','flow quantity_y'])
    else:
        if verbose == 1:
            print('pylca_celavi_background_postprocess: no insitu emissions')
        
    return final_res


def impact_calculations(final_res,traci_lci_filename):    
    """
    Converts pollutant mass flows to environmental impacts using the TRACI 2.1 midpoint characterization method.

    Parameters
    ----------
    final_res: pandas.DataFrame
       Total (insitu and background) pollutant mass flows.
    
    traci_lci_filename: str
       Filename where the TRACI characterization factors are stored.
    
    Returns
    -------
    pandas.DataFrame
        Total environmental impacts.
        Columns:
            - year: int
                Model year.
            - facility_id: int
                Facility ID.
            - material: str
                Name of material being processed.
            - route_id: str
                UUID of transportation route.
            - state: str
                State in which facility is located.
            - stage: str
                Supply chain stage.
            - impacts: str
                Name of environmental impact.
            - impact: float
                Environmental impact quantity.
    """     
   
    traci = pd.read_csv(traci_lci_filename)
    traci = traci.fillna(0)
    impacts = list(traci.columns)
    valuevars = ['Global Warming Air (kg CO2 eq / kg substance)',
     'Acidification Air (kg SO2 eq / kg substance)',
     'HH Particulate Air (PM2.5 eq / kg substance)',
     'Eutrophication Air (kg N eq / kg substance)',
     'Eutrophication Water (kg N eq / kg substance)',
     'Ozone Depletion Air (kg CFC-11 eq / kg substance)',
     'Smog Air (kg O3 eq / kg substance)',
     'Ecotox. CF [CTUeco/kg], Em.airU, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.airC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.fr.waterC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.sea waterC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.nat.soilC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.agr.soilC, freshwater',
     'Human health CF  [CTUcancer/kg], Emission to urban air, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to urban air, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. rural air, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. rural air, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. freshwater, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. freshwater, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. sea water, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. sea water, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. natural soil, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. natural soil, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. agric. Soil, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. agric. Soil, non-canc.']
    
    
    traci_df = pd.melt(traci, id_vars=['CAS #', 'Formatted CAS #', 'Substance Name'], value_vars=valuevars, var_name='impacts', value_name='value')
    final_res['flow name'] = final_res['flow name'].str.upper()
    df_lcia = final_res.merge(traci_df, left_on=['flow name'], right_on=['Substance Name'])
    df_lcia['impact'] = df_lcia['flow quantity'] * df_lcia['value']
    df_lcia = df_lcia.groupby(['year', 'facility_id', 'material', 'route_id', 'state', 'stage', 'impacts'],dropna=False)['impact'].agg('sum').reset_index()

    return df_lcia                      

