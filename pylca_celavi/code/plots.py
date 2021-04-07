#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 19:55:58 2020

@author: tghosh
"""


import pickle
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import seaborn as sns


#%%
def graph(material ='glass fiber reinforced polymer', stage = 'manufacturing', scenario = 'bau', coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = None,impact = None):
    df = df[df['material'] == material]
    df = df[df['stage'] == stage]
    df = df[df['scenario'] == scenario]
    df = df[df['coarse grinding location'] == coarse_grinding_location]
    df = df[df['distance to recycling facility'] == distance_to_recycling_facility]
    df = df[df['distance to cement plant'] == distance_to_cement_plant]
    
    if df.empty == False:
        df.to_csv('Check.csv')
        df.plot(x = 'year', y = 'impact', kind = 'line', title = impact+ material +' '+ stage +' '+ scenario)
        return df


plt.style.use('ggplot')
traci = pd.read_csv('traci21.csv')
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


valuevars = ['Acidification Air (kg SO2 eq / kg substance)']

traci_df = pd.melt(traci, id_vars=['CAS #','Formatted CAS #','Substance Name'], value_vars=valuevars, var_name='impacts', value_name='value')

final_lci_result = pd.read_csv('final_lci_results_processed_multi.csv')
final_lci_result['flow name'] =   final_lci_result['flow name'].str.upper()                                 
                                   
#impacts = ['Global Warming Air (kg CO2 eq / kg substance)']                                   
for im in valuevars:
   df =  traci_df[traci_df['impacts'] == im] 
   graph_df_lcia = final_lci_result.merge(df, left_on = ['flow name'], right_on = ['Substance Name'])
   graph_df_lcia['impact'] = graph_df_lcia['flow quantity'] * graph_df_lcia['value']
   graph_df_lcia = graph_df_lcia.groupby(['year', 'material','stage','scenario', 'coarse grinding location',
       'distance to recycling facility', 'distance to cement plant',
       'flow unit', 'impacts'])['impact'].agg('sum').reset_index()
   
    

    for stg in list(pd.unique(graph_df_lcia['stage'])):
       for scene in list(pd.unique(graph_df_lcia['scenario'])):
           for mat in list(pd.unique(graph_df_lcia['material'])):

                 chk = graph(material = mat, stage = stg,scenario = scene, coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = graph_df_lcia,impact = im)
                                 


sys.exit(0)
#%%
sns.set_style("ticks")
sns.set_context("talk")
sns.color_palette('bright')


traci = pd.read_csv('traci21.csv')
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


traci_df = pd.melt(traci, id_vars=['CAS #','Formatted CAS #','Substance Name'], value_vars=valuevars, var_name='impacts', value_name='value')

def graph(material ='glass fiber reinforced polymer', stage = 'manufacturing', coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = None,impact = None, ax = None):
    df = df[df['material'] == material]
    df = df[df['stage'] == stage]
    df = df[df['coarse grinding location'] == coarse_grinding_location]
    df = df[df['distance to recycling facility'] == distance_to_recycling_facility]
    df = df[df['distance to cement plant'] == distance_to_cement_plant]
    
    if df.empty == False:
        df.to_csv('Check.csv')
        sns.lineplot(ax = ax,data = df, x = 'year', y = 'impact', legend = False, hue = 'scenario',palette='bright')
        title = impact[0:30]+'\n'+impact[30:]
        ax.set_title(title)
        return df
    

def graph2(material ='glass fiber reinforced polymer',  scenario = 'bau', coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = None,impact = None):
    df = df[df['material'] == material]
    df = df[df['scenario'] == scenario]
    df = df[df['coarse grinding location'] == coarse_grinding_location]
    df = df[df['distance to recycling facility'] == distance_to_recycling_facility]
    df = df[df['distance to cement plant'] == distance_to_cement_plant]
    
    if df.empty == False:

        df.plot(x = 'year', y = 'impact', kind = 'line', title = impact+ material +' ' +' '+ scenario)
        return dfs

final_lci_result = pd.read_csv('final_lci_results_processed_multi.csv')
#final_lci_result = final_lci_result[(final_lci_result['stage'] == 'landfilling') | (final_lci_result['stage'] == 'recycle to raw material')]
final_lci_result['flow name'] =   final_lci_result['flow name'].str.upper() 


fig1, ax1 = plt.subplots(5,5,figsize = (40, 30))
fig1.tight_layout(pad=3.0)



c = 0
b = 0


stg  = 'landfilling'
mat = 'concrete'
for im in valuevars:
   df =  traci_df[traci_df['impacts'] == im] 
   graph_df_lcia = final_lci_result.merge(df, left_on = ['flow name'], right_on = ['Substance Name'])
   graph_df_lcia['impact'] = graph_df_lcia['flow quantity'] * graph_df_lcia['value']
   
   graph_df_lcia1 = graph_df_lcia.groupby(['year', 'material','scenario', 'coarse grinding location',
       'distance to recycling facility', 'distance to cement plant',
       'flow unit', 'impacts'])['impact'].agg('sum').reset_index()
   
   graph_df_lcia2 = graph_df_lcia.groupby(['year', 'material','stage','scenario', 'coarse grinding location',
       'distance to recycling facility', 'distance to cement plant',
       'flow unit', 'impacts'])['impact'].agg('sum').reset_index()
   graph_df_lcia1['stage'] = 'Total'
   #chk = graph2(material = 'glass fiber reinforced polymer', scenario = 'bau', coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = graph_df_lcia1,impact = im)
   chk = graph(material = mat, stage = stg, coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = graph_df_lcia1,impact = im, ax = ax1[b,c])
   #chk = graph(material = mat, stage = stg, coarse_grinding_location = 'onsite',distance_to_recycling_facility = 51, distance_to_cement_plant = 204,df = graph_df_lcia2,impact = im, ax = ax1[b,c])
    
    
   c = c+1
   if c == 5:
       b = b+1
       c = 0
       
fig1.tight_layout() 
fig1.subplots_adjust(bottom=0.06)  
fig1.legend(['bau','hc','mc'],loc="lower center", ncol=3)   
                          
fig1.suptitle(stg+' '+mat,x = 0.5, y = 0.03)

#%%


'''
def traci_lcia_search():
    #Change the column to whichever indicator is unders study
    ghg = traci[traci['Global Warming Air (kg CO2 eq / kg substance)'] >= 1]
    emissions = list(pd.unique(final_lci_result['product'].str.upper()))
    emission_traci = list(pd.unique(ghg['Substance Name']))
    search_l1 = []
    search_l2 = []
    search_l3 = []
    search_l4 = []
    for i in emissions:
        #print(i)
        res = search.extract(i, emission_traci, limit = 3)
        search_l1.append(i)
        search_l2.append(res[0][0])
        search_l3.append(res[1][0])
        search_l4.append(res[2][0])
    
    search_df = pd.DataFrame({'search':search_l1,'one':search_l2,'two':search_l3,'three':search_l4})
    #Change file name
    search_df.to_excel('gwp_traci_flows.xlsx')

def ghg_lcia(graph_df):
    traci_bridge = pd.read_excel('gwp_traci_matched_flows.xlsx',sheet_name = 'Sheet2')
    ghg = traci[traci['Global Warming Air (kg CO2 eq / kg substance)'] >= 1]
    traci_ghg = traci_bridge.merge(ghg, left_on = 'search', right_on = 'Substance Name')
    graph_df_lcia = graph_df.merge(traci_ghg,left_on = 'flow name',right_on = 'FINAL')
    graph_df_lcia['gwp'] = graph_df_lcia['flow quantity'] * graph_df_lcia['Global Warming Air (kg CO2 eq / kg substance)']
    graph_df_lcia = graph_df_lcia[['flow name','gwp','year','stage','material','scenario','coarse grinding location','distance to recycling facility','distance to cement plant']]
    gwp_df_lcia = graph_df_lcia.groupby(by = ['year','stage','material','scenario','coarse grinding location','distance to recycling facility','distance to cement plant'])['gwp'].agg('sum')
    return gwp_df_lcia



def normalize(lci_result):
    results2020 = lci_result[lci_result['year'] == 2020]
    results2020['gwp1'] = results2020['gwp']
    results2020['year1']= results2020['year']
    del results2020['gwp']
    del results2020['year']
    
    norm_lci_result = lci_result.merge(results2020, on = ['stage'], how = 'left', indicator = True)
    norm_lci_result['gwp'] = norm_lci_result ['gwp']/norm_lci_result ['gwp1']
    del norm_lci_result ['gwp1']
    del norm_lci_result ['year1']
    return norm_lci_result.dropna()

def normalize_cap(lci_result):
    
    cap= pd.read_excel('total_cap_wind.xlsx')
    lci_result['year1'] = lci_result['year']
    lci_result['year'] = lci_result['year'].astype(int)  
    cap['year'] = cap['year'].astype(int)
    norm_lci_result = lci_result.merge(cap, left_on = ['year'],right_on = ['year'], how = 'left', indicator = True)
    norm_lci_result['gwp/GW'] = norm_lci_result ['gwp']/norm_lci_result ['total_cap']    
    norm_lci_result['year'] = norm_lci_result['year1']
    return norm_lci_result
    del norm_lci_result['gwp']
    del norm_lci_result['year1']
    return norm_lci_result.dropna()


def glass_fiber(final_lci_result):

    #Graph
    #graph_df = final_lci_result[final_lci_result['product'] == 'Carbon dioxide, fossil']
    final_lci_result['product'] = final_lci_result['product'].str.upper()
    graph_df = ghg_lcia(final_lci_result).reset_index()
    graph_df = normalize_cap(graph_df)
    graph_df_extraction = graph_df[graph_df['stage'] == 'extraction and production']
    graph_df_recycling = graph_df[graph_df['stage'] == 'recycling']
    res_celavi = pd.read_csv('celavi_results_glass_fiber.csv')
    df_mat = res_celavi[res_celavi['material'] == 'glass fiber reinforced polymer']
    
    
    res = pd.concat([graph_df_extraction,graph_df_recycling])
    res = res.pivot_table(columns = 'stage',index = 'year', values = 'gwp/GW').fillna(0)
    a1 = []
    b1=[]
    result = pd.DataFrame(columns = ['year','extraction and production', 'recycling'])
    for i in res.itertuples():
        a1.append(i[1])
        b1.append(i[2])
        if i[0] % 1 == 0.75:
            result = result.append({'year' : str(int(i[0])), 'extraction and production' : sum(a1), 'recycling' : sum(b1)}, ignore_index = True)
            #result = result.set_index('year')
            a1 = []
            b1 = []  
    
    #result = pd.DataFrame(list(year),list(extraction_and_production),list(recycling))
    #result =  result.set_index('year')
    #result.plot(kind = 'bar', stacked = True, figsize=(20,5))
    #plt.savefig('glass_fiber.pdf')
    #result2.plot(kind = 'bar', stacked = True)
    df_extraction = df_mat[df_mat['process'] == 'extraction and production']
    df_extraction = df_extraction[df_extraction['input name'] == 'glass fiber']
    df_recycling = df_mat[df_mat['process'] == 'recycling']    
    df_recycling = df_recycling[df_recycling['input name'] == 'electricity']

    
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    fig1, ax1 = plt.subplots()
    #graph_df  = graph_df[graph_df['value'] > 0.01]

    ax1.plot(graph_df_extraction['year'],graph_df_extraction['gwp/GW'], label = 'extraction')
    ax1.plot(graph_df_recycling['year'],graph_df_recycling['gwp/GW'],label = 'recycling')
    
    ax1.legend()
    plt.title('gwp', fontdict=None, loc='center', pad=None)
    plt.show()
    #fig1.savefig('co2.pdf',bbox_inches="tight", dpi = 500) 
    
    fig2, ax2 = plt.subplots()
    ax2.plot(df_extraction['model time'],df_extraction['quantity'],label = 'glass fiber virgin')
    ax2.plot(df_recycling['model time'],df_recycling['quantity'],label = 'electricity')
    ax2.legend()
    plt.show()



def cumulative_emissions(graph_df):
    
    fd_cur = graph_df.groupby(by = ['stage','scenario','coarse grinding location','distance to recycling facility','distance to cement plant'])['gwp'].agg('sum').reset_index()
    fd_cur.to_csv('cumulative_processed_GWP.csv')
    fd_manuf = fd_cur[fd_cur['stage'] == 'manufacturing']
    fd_transport = fd_cur[fd_cur['stage'] == 'transportation']
    fd_fine = fd_cur[fd_cur['stage'] == 'fine grinding']
    fd_transport_fine = fd_cur[(fd_cur['stage'] == 'transportation') | (fd_cur['stage'] == 'fine grinding')]
    fd_transport_fine = fd_transport_fine.groupby(by = ['scenario'])['gwp'].agg('sum').reset_index()
    #return fd_transport_fine
    fd_coarse = fd_cur[fd_cur['stage'] == 'coarse grinding']
    fd_land = fd_cur[fd_cur['stage'] == 'landfilling']
    fd_coarse_land = fd_cur[(fd_cur['stage'] == 'coarse grinding') | (fd_cur['stage'] == 'landfilling')]
    fd_coarse_land = fd_coarse_land.groupby(by = ['scenario'])['gwp'].agg('sum').reset_index()    
    
    stage = list(pd.unique(fd_cur['stage']))
    
    fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize = (20,10))
    ax1.bar(x="scenario", height="gwp", data=fd_manuf,color = 'lightsalmon')
    #ax1.bar(x="scenario", height="gwp", data=fd_transport,color = 'red')
    ax1.set_title('Cumulative GWP Impact \n Manufacturing',fontdict=None, pad=None)
    ax1.set_ylabel('kgCO2eq.')
    ax1.set_xlabel('scenario')
    
    ax2.bar(x="scenario", height="gwp", data=fd_transport_fine,color = 'deepskyblue')
    ax2.bar(x="scenario", height="gwp", data=fd_fine,color = 'coral')    
    labels = ['Transportation','Fine grinding']
    ax2.legend(loc = 'upper right',labels = labels)
    ax2.set_title('Cumulative GWP Impact',fontdict=None, pad=None)
    ax2.set_xlabel('scenario')
    #plt.ylabel('kgCO2eq.')
    #plt.xlabel('scenario')    
    



    ax3.bar(x="scenario", height="gwp", data=fd_coarse_land,color = 'lightcoral')
    ax3.bar(x="scenario", height="gwp", data=fd_coarse, color = 'cornflowerblue')    
    ax3.set_title('Cumulative GWP Impact',fontdict=None, pad=None)
    labels = ['Landfilling','Coarse grinding']
    ax3.legend(loc = 'upper right',labels = labels)
    ax2.set_xlabel('scenario')
    #plt.ylabel('kgCO2eq.')
    #plt.xlabel('scenario') 

    

    for j in stage:               
         fd_cur2 = fd_cur[fd_cur['stage'] == j]
         
         plt.rcParams["font.weight"] = "bold"
         plt.rcParams["axes.labelweight"] = "bold"
         fig1, ax1 = plt.subplots(figsize=(5,5))
         
         ax = sns.barplot(x="scenario", y="gwp", data=fd_manuf)
         plt.xlabel('scenario')
         plt.ylabel('kgCO2eq.')
         ax1.legend(loc = 'upper right')
         plt.title(j, fontdict=None, pad=None,fontweight='bold')         
         plt.show()
            

    fig1.savefig('cumulative.png',bbox_inches="tight", dpi = 500)  
    #fig2.savefig('transfineccumulative.png',bbox_inches="tight", dpi = 500) 
    #fig3.savefig('coarselandfillingccumulative.png',bbox_inches="tight", dpi = 500) 

def material(final_lci_result):

    #Graph
    #graph_df = final_lci_result[final_lci_result['product'] == 'Carbon dioxide, fossil']
    final_lci_result['flow name'] = final_lci_result['flow name'].str.upper()
    graph_df = ghg_lcia(final_lci_result).reset_index()
    graph_df.to_csv('GWP_results.csv', index = False)
    #return cumulative_emissions(graph_df)    
    fd_cur = normalize_cap(graph_df)
    return fd_cur    
    stage = list(pd.unique(fd_cur['stage']))
    print(stage)
    for j in stage:
                             
                fd_cur2 = fd_cur[fd_cur['stage'] == j]
                material = list(pd.unique(fd_cur2['material']))
                for k in material:
                    fd_cur3 = fd_cur2[fd_cur2['material'] == k]
                    scenario = list(pd.unique(fd_cur3['scenario']))
                    #for l in scenario:
                    #    fd_cur4 = fd_cur3[fd_cur3['scenario'] == l]       
                    #    fd_cur5 = fd_cur4[['gwp/GW','stage','material','scenario','year']]
                    hc = fd_cur3[fd_cur3['scenario'] == 'hc']
                    bau = fd_cur3[fd_cur3['scenario'] == 'bau'] 
                    mc = fd_cur3[fd_cur3['scenario'] == 'mc'] 

                #    res_celavi = pd.read_csv('celavi_results_glass_fiber.csv')
                #    df_mat = res_celavi[res_celavi['material'] == 'glass fiber reinforced polymer']
                
                
                #    res = pd.concat([graph_df_extraction,graph_df_recycling])
                #    res = res.pivot_table(columns = 'stage',index = 'year', values = 'gwp/GW').fillna(0)
                #    a1 = []
                #    b1=[]
                ##    result = pd.DataFrame(columns = ['year','extraction and production', 'recycling'])
                 #   for i in res.itertuples():
                #        a1.append(i[1])
                #        b1.append(i[2])
                #        if i[0] % 1 == 0.75:
                #            result = result.append({'year' : str(int(i[0])), 'extraction and production' : sum(a1), 'recycling' : sum(b1)}, ignore_index = True)
                #            #result = result.set_index('year')
                #            a1 = []
                #            b1 = []  
    
                #result = pd.DataFrame(list(year),list(extraction_and_production),list(recycling))
                #result =  result.set_index('year')
                #result.plot(kind = 'bar', stacked = True, figsize=(20,5))
                #plt.savefig('glass_fiber.pdf')
                #result2.plot(kind = 'bar', stacked = True)
            #    df_extraction = df_mat[df_mat['process'] == 'extraction and production']
            #    df_extraction = df_extraction[df_extraction['input name'] == 'glass fiber']
            #    df_recycling = df_mat[df_mat['process'] == 'recycling']    
            #    df_recycling = df_recycling[df_recycling['input name'] == 'electricity']

    
                    #plt.rcParams["font.weight"] = "bold"
                    #plt.rcParams["axes.labelweight"] = "bold"
                    fig1, ax1 = plt.subplots()
                    #graph_df  = graph_df[graph_df['value'] > 0.01]
                    
                    ax1.plot(hc['year'],hc['gwp/GW'], label = 'hc')
                    ax1.plot(mc['year'],mc['gwp/GW'], label = 'mc')
                    ax1.plot(bau['year'],bau['gwp/GW'], label = 'bau')
                    #ax1.plot(graph_df_recycling['year'],graph_df_recycling['gwp/GW'],label = 'recycling')
                    plt.xlabel('year')
                    plt.ylabel('kgCO2eq.')
                    ax1.legend(loc = 'upper right')
                    plt.title(j+' '+k, fontdict=None, pad=None)
                    plt.show()
                    fig1.savefig(j+' '+k+'.pdf',bbox_inches="tight", dpi = 500) 
                        
                    #fig2, ax2 = plt.subplots()
                    #ax2.plot(df_extraction['model time'],df_extraction['quantity'],label = 'glass fiber virgin')
                    #ax2.plot(df_recycling['model time'],df_recycling['quantity'],label = 'electricity')
                    #ax2.legend()
                    #plt.show()

 





final_lci_result = pd.read_csv('final_lci_results_processed_multi.csv')
chk = material(final_lci_result)
#final_lci_result = pd.read_csv('final_lci_result_steel.csv')
#2012 is not working
#final_lci_result = final_lci_result[(final_lci_result['year'] > 2000) & (final_lci_result['year'] < 2014)]
#normalized_results = normalize(final_lci_result)
#chk = final_lci_result.merge(normalized_results, on = ['product','unit','stage','year','value'], indicator = True)
#chk = steel(final_lci_result)











def steel(final_lci_result):

    #Graph
    graph_df = final_lci_result[final_lci_result['product'] == 'Carbon dioxide, fossil']
    final_lci_result['product'] = final_lci_result['product'].str.upper()
    graph_df = ghg_lcia(final_lci_result).reset_index()
    
    graph_df = normalize_cap(graph_df)
    graph_df_extraction = graph_df[graph_df['stage'] == 'manufacturing linear']
    graph_df_recycling = graph_df[graph_df['stage'] == 'manufacturing recycled']
    res_celavi = pd.read_csv('celavi_lci_steel_base.csv')
    df_mat = res_celavi[res_celavi['material'] == 'steel']
    
    input_material = 'coal'
    df_extraction = df_mat[df_mat['process'] == 'manufacturing linear']
    df_extraction = df_extraction[df_extraction['input name'] == input_material]
    df_recycling = df_mat[df_mat['process'] == 'manufacturing recycled']
    df_recycling = df_recycling[df_recycling['input name'] == input_material]


    res = pd.concat([graph_df_extraction,graph_df_recycling])
    
    res = res.pivot_table(columns = 'stage',index = 'year', values = 'gwp/GW').fillna(0)
    a1 = []
    b1=[]
    result = pd.DataFrame(columns = ['year','manufacturing linear', 'manufacturing recycled'])
    for i in res.itertuples():
        a1.append(i[1])
        b1.append(i[2])
        if i[0] % 1 == 0.75:
            result = result.append({'year' : str(int(i[0])), 'manufacturing linear' : sum(a1), 'manufacturing recycled' : sum(b1)}, ignore_index = True)
            #result = result.set_index('year')
            a1 = []
            b1 = []  
    
    #result = pd.DataFrame(list(year),list(extraction_and_production),list(recycling))
    #result =  result.set_index('year')
    #result.plot(kind = 'bar', stacked = True, figsize=(20,5))
    #plt.savefig('steel.pdf')

    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    fig1, ax1 = plt.subplots()
    #graph_df  = graph_df[graph_df['value'] > 0.01]
    ax1.plot(graph_df_extraction['year'],graph_df_extraction['gwp/GW'], label = 'linear')
    ax1.plot(graph_df_recycling['year'],graph_df_recycling['gwp/GW'],label = 'recycling')
    
    ax1.legend()
    plt.title('gwp', fontdict=None, loc='center', pad=None)
    plt.show()
    #fig1.savefig('co2.pdf',bbox_inches="tight", dpi = 500) 
    
    fig2, ax2 = plt.subplots()
    ax2.plot(df_recycling['model time'],df_recycling['quantity'],label = input_material + ' recycled')
    ax2.plot(df_extraction['model time'],df_extraction['quantity'],label = input_material + ' linear')
    ax2.legend()
    plt.show()   
'''