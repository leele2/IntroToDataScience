# -*- coding: utf-8 -*-
"""
Created on Sun Aug  8 01:34:41 2021

@author: dj-lu
"""

import geopandas
import csv
import json
import pandas as pd
import os
import zipfile

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="example app")

import time
time_start = time.time()

#Creating function to unzip files and import .json files to dict
def load_data(JobStep=1, Files_to_Unzip=0, Dir='JobAds'):
    #Creating List of files in Dir **ALL files MUST be .zip**
    files = os.listdir('%s' % (Dir))
    #Default number of files to unzip is ALL
    if (Files_to_Unzip == 0):
        Files_to_Unzip = len(files)
    #Creating Dictonary to hold data    
    dictonary = {}
    #Fields to be removed
    removed_fields = ['jobId', 'applicationCount', 'contractType',
                      'expirationDate', 'externalUrl', 'jobUrl',
                      'maximumSalary', 'minimumSalary', 'salary']
    #Unzipping and reading json files
    for zip_file in files[:Files_to_Unzip]:
        with zipfile.ZipFile("./JobAds/%s" % (zip_file)) as zip_file_obj:
            filelist = sorted(zip_file_obj.namelist())[1::JobStep]
            for filename in filelist:
                with zip_file_obj.open(filename) as zipped_file:
                    unzipped_file = zipped_file.read()
                    data = json.loads(unzipped_file.decode("utf-8"))
                    if not data['jobId'] == 0:
                        for i in removed_fields:
                            del data[i]
                        dictonary[filename[4:]] = data
    return dictonary

#Loading list of places with matching counties
place_to_county = {}
places = []
with open('MapBoundaries/2019/IPN_GB_2019/IPN_GB_2019.csv',
          newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # if row['place18nm'] not in places:
        #     places.append(row['place18nm'])
        #     place_to_county[row['place18nm']] = row['cty18nm']
        if (row['place18nm'] not in places) and (not row['lad18nm'] is None):
            places.append(row['place18nm'])
            place_to_county[row['place18nm']] = row['lad18nm']

counties_list = []
for i in place_to_county.values():
    if i not in counties_list:
        counties_list.append(i)

#Loading Ad Data
data = load_data(1)

#Loading Geo Data
path = "MapBoundaries/2019/Counties_and_Unitary_Authorities_(December_2019)_B"\
    "oundaries_UK_BUC.geojson"
gdf = geopandas.read_file(path)
boundary_list = gdf['ctyua19nm'].values.tolist()

#Processing Ad Data
county_freq = {i : 0 for i in boundary_list}
location_list = []
for i in data:
    if data[i]['locationName'].title() in boundary_list:
        county_freq[data[i]['locationName'].title()] = county_freq.get(
            data[i]['locationName'], 0) + 1
    County = place_to_county.get(data[i]['locationName'].title(), 0)
    if County in boundary_list:
        county_freq[County] = county_freq.get(County, 0) + 1
    if not data[i]['locationName'] in location_list:
        location_list.append(data[i]['locationName'])

check_me = []
for i in location_list:
    if not i in [ i in place_to_county.keys()] and not i in boundary_list:
        check_me.append(i)

num_ads_located = sum([ i for i in county_freq.values()])
num_of_ads = len(data)

#Creating Data Frame from Ads
df = pd.DataFrame.from_dict(county_freq, orient = 'index').reset_index(
    ).rename(columns = {'index' : 'ctyua19nm', 0 : 'Frequency'})

merged = gdf.merge(df, on = 'ctyua19nm')
merged.plot(column='Frequency', legend = True, figsize=(15,10))

print("\n\nTime to run = %.3f(s)" % (time.time() - time_start))