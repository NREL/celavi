#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 20:53:43 2021

@author: tghosh
"""

import matplotlib.pyplot as plt
import geopandas as gp
import geoplot as gplt
import geoplot.crs as gcrs
import matplotlib
matplotlib.rcdefaults() 
import shapefile as shp
import contextily as ctx
import pandas as pd
import sys
from shapely.geometry import Point


shp_path = './texasshp/State.shp'
#shp_path = './egrid2018_subregions/eGRID2018 Subregions.shp'
sf = gp.read_file(shp_path)
 

df = pd.read_excel('landfilldata.xlsx')

geometry = [Point(xy) for xy in zip(df['LON'],df['LAT'])]


def read_shapefile(sf):
        """
        Read a shapefile into a Pandas dataframe with a 'coords' 
        column holding the geometry information. This uses the pyshp
        package
        """
        fields = [x[0] for x in sf.fields][1:]
        records = sf.records()
        shps = [s.points for s in sf.shapes()]    
        df = pd.DataFrame(columns=fields, data=records)
        df = df.assign(coords=shps)
        return df

df = sf 
geo_df = gp.GeoDataFrame(geometry = geometry)


#geo_df = geo_df.to_crs(epsg=3857)   
#sf = sf.to_crs(epsg=3857)    
#ax = gplt.polyplot(sf, projection=gplt.crs.Orthographic(), figsize=(4, 4))
#ax = sf.plot(alpha=0.35, color='#d66058', zorder=1)
ax = sf.plot(figsize=(10, 10), alpha=0.5, edgecolor='k')
#ctx.add_basemap(ax)
ax = gp.GeoSeries(sf['geometry'].unary_union).boundary.plot(ax=ax, alpha=0.5, color="#ed2518",zorder=2)
ax = geo_df.plot(ax = ax, markersize = 30, color = 'red',marker = '*',label = 'Landfills', zorder=3)

vf = pd.read_excel('wind_turbines_tx.xlsx')
geometry = [Point(xy) for xy in zip(vf['xlong'],vf['ylat'])]
geo_df = gp.GeoDataFrame(geometry = geometry)
geo_df.crs = {'init':"epsg:3857"}
ax = geo_df.plot(ax = ax, markersize = 5, color = 'blue',marker = '.',label = 'WindTurbines', zorder=3)


cf = pd.read_excel('cement_facilities.xlsx')
geometry = [Point(xy) for xy in zip(cf['LONGITUDE83'],cf['LATITUDE83'])]
geo_df = gp.GeoDataFrame(geometry = geometry)
geo_df.crs = {'init':"epsg:3857"}
ax = geo_df.plot(ax = ax, markersize = 40, color = 'black',marker = '^',label = 'Cement Facilities', zorder=3)
ax.legend()

plt.savefig('TexasMap.pdf',bbox_inches = 'tight', pad_inches = 0 , ppi = 100)

#ctx.add_basemap(ax)