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

town_to_county = {}
town_list = []
county_list = []

#Loading list of towns with matching counties
with open('Towns_List.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['Country'] == 'England' or row['Country'] == 'Wales':
            town_list.append(row['Town'])
            town_to_county[row['Town']] = row['County']
            if not row['County'] in county_list:
                   county_list.append(row['County'])

#Loading Ad Data
data = load_data(20,100)

#Loading Geo Data
path = "MapBoundaries/Counties_and_Unitary_Authorities_(December_2016)_Boundaries.geojson"
gdf = geopandas.read_file(path).rename(columns = {'ctyua16nm' : 'Town'})
region_list = gdf['Town'].values.tolist()


#Using to Geopy to match regions with areas
region_to_area={}
# for i in region_list:
#     region_to_area[i] = geolocator.geocode(i).address.split(', ')[1]
#
# with open('Region_to_area.tsv', 'w') as f:
#     for key in region_to_area.keys():
#         f.write("%s\t%s\n"%(key,region_to_area[key]))
with open('Region_to_area.tsv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter = '\t')
    for row in reader:
        region_to_area[row[0]] = row[1]



#Processing Ad Data
county_freq = {i : 0 for i in region_list}
location_list = []
for i in data:
    if data[i]['locationName'].title() in region_list:
        county_freq[data[i]['locationName'].title()] = county_freq.get(data[i]['locationName'], 0) + 1
    County = town_to_county.get(data[i]['locationName'].title(), 0)
    if County in region_list:
        county_freq[County] = county_freq.get(County, 0) + 1
    if not data[i]['locationName'] in location_list:
        location_list.append(data[i]['locationName'])

check_me = []
for i in location_list:
    if not i in [ i in town_to_county.keys()] and not i in region_list:
        check_me.append(i)

num_ads_located = sum([ i for i in county_freq.values()])
num_of_ads = len(data)

#Creating Data Frame from Ads
df = pd.DataFrame.from_dict(county_freq, orient = 'index').reset_index(
    ).rename(columns = {'index' : 'Town', 0 : 'Frequency'})

merged = gdf.merge(df, on = 'Town')
merged.plot(column='Frequency', legend = True, figsize=(30,20))
merged['Area'] =  [i for i in region_to_area.values()]
merged_area = merged.dissolve(by = 'Area', aggfunc = 'sum')
merged_area.plot(column='Frequency', legend = True, figsize=(30,20))