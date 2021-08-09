import geopandas

path = "C:/Users/dj-lu/OneDrive - University of Exeter/University of Exeter/04 - Fourth Year/Introduction to Data Science/Coursework/Coursework 2/MapBoundaries/Counties_and_Unitary_Authorities_(December_2016)_Boundaries.geojson"

gdf = geopandas.read_file(path).rename(columns = {'ctyua16nm' : 'Town'})


import json
import pandas as pd
import os
import zipfile


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

town_list = pd.read_csv("Towns_List.csv")
town_list = town_list.drop(town_list[
    (town_list.Country == 'Scotland') | 
    (town_list.Country == 'Northern Ireland')].index)



#Loading Data
data = load_data(1,1)

#Processing Data
county_freq = {}
for i in data:
    if data[i]['locationName'].lower() in town_list['Town'].str.lower().values:
        county = town_list[town_list.Town.str.lower() == data[i]['locationName'].lower()][
            'County'].values[0]
        county_freq[county] = county_freq.get(county, 0) + 1

df = pd.DataFrame.from_dict(county_freq, orient = 'index').reset_index().rename(columns = {'index' : 'Town', 0 : 'Frequency'})

gdf.rename(columns = {'ctyua16nm' : 'Town'})

merged = gdf.merge(df, on = 'Town')
merged.plot()