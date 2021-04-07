#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 15:33:28 2020

@author: tghosh
"""

import pickle
import sys
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import os


def postprocessing():
    #Giving names to the columns for the final result file
    final_res = pd.read_csv('lci_temp.csv',header = None)
    column_names = ['flow name','flow unit','flow quantity','year','stage','material','scenario','coarse grinding location','distance to recycling facility','distance to cement plant']
    final_res.columns = list(column_names)
    final_res.to_csv('lci_results_processed_multi.csv', index = False)
    
    
    
    
    #Adding up the insitu emission primariy for the cement manufacturing process
    column_names = ['flow name','flow unit','year','stage','material','scenario','coarse grinding location','distance to recycling facility','distance to cement plant']
    insitu = pd.read_csv('process_emission_insitu.csv')
    final_res['flow name'] = final_res['flow name'].str.lower()
    total_em = insitu.merge(final_res,on = column_names,how = 'outer')
    total_em = total_em.fillna(0)
    total_em['flow quantity'] = total_em['flow quantity_x'] + total_em['flow quantity_y']
    total_em = total_em.drop(columns = ['flow quantity_x','flow quantity_y','direction'])
    total_em.to_csv('final_lci_results_processed_multi.csv', index = False)
    
    
    
    #Giving names to the columns for the final result file
    final_res = pd.read_csv('lciflow_temp.csv',header = None)
    column_names = ['flow name','flow unit','flow quantity','year','stage','material','scenario','coarse grinding location','distance to recycling facility','distance to cement plant']
    final_res.columns = list(column_names)
    final_res.to_csv('lciflow_results_processed_multi.csv', index = False)

    os.remove('lci_temp.csv')
    os.remove('lciflow_temp.csv')