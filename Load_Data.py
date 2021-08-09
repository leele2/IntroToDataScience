# -*- coding: utf-8 -*-
"""
Created on Tue Jul 20 20:44:49 2021

@author: dj-lu
"""
import json
import numpy as np
import matplotlib as mpl
import os
import pandas as pd
import requests
import zipfile

from bs4 import BeautifulSoup
from datetime import datetime
from matplotlib import pyplot as plt
from scipy import stats
from wordcloud import WordCloud

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


#Loading Data
data = load_data(1)

Day_freq = {}
Bigrams_freq = {}
Currency_freq = {}
Employer_freq = {}
Nurse_ads = {}
Nurse_descr = []
Mean_salaries = []
Full_time_jobs = {}
Part_time_jobs = {}
Both_time_jobs = {}
Neither_time_jobs = {}


check_me = {}

CurrencyRates = requests.get('http://www.floatrates.com/daily/gbp.json').json()
CurrencyRates = {k.upper(): v for k, v in CurrencyRates.items()}

#Processing Data
for i in data:
    if data[i]['yearlyMaximumSalary'] == 0:
        check_me[i] = data[i]
    #Dictionary counting job ads on each day
    Day_freq[data[i]['datePosted']] = Day_freq.get(
        data[i]['datePosted'], 0) + 1
    #Dictionary counting Nurse ads on days
    if 'nurse' in data[i]['jobTitle'].lower().replace('nursery',''
                                            ).replace('non nurse',''
                                            ).replace('non-nurse',''):
        Nurse_descr.append(BeautifulSoup(data[i]['jobDescription']).get_text())
        Nurse_ads[data[i]['datePosted']] = Nurse_ads.get(
            data[i]['datePosted'], 0) + 1
    #Dictionary counting currency types
    Currency_freq[data[i]['currency']] = Currency_freq.get(
        data[i]['currency'], 0) + 1
    #Dictionary counting job ads by each employer
    Employer_freq[(data[i]['employerId'], data[i]['employerName'])] = Employer_freq.get(
        (data[i]['employerId'], data[i]['employerName']), 0) + 1
    #Dictionary of Bigrams
    Job_title_words = data[i]['jobTitle'].replace('-', '').strip().split()
    for word1, word2 in zip(Job_title_words[:-1], Job_title_words[1:]):
        Bigrams_freq[(word1, word2)] = Bigrams_freq.get(
            (word1, word2), 0) + 1
    #List of Advertised Annual Salary
    if data[i]['currency'] is not None and not (
            data[i]['yearlyMaximumSalary'] == 0 and
            data[i]['yearlyMinimumSalary'] == 0):
        Mean_yearly_salary = (data[i]['yearlyMaximumSalary']
                              + data[i]['yearlyMinimumSalary'])/2
        if not data[i]['currency'] == 'GBP':
            Mean_yearly_salary = CurrencyRates[
                data[i]['currency']]['inverseRate']*Mean_yearly_salary
        Mean_salaries.append(round(Mean_yearly_salary, 2))
    #Subset of data
    if data[i]['fullTime'] and data[i]['partTime']:
        Both_time_jobs[i] = data[i]
        continue
    elif data[i]['fullTime']:
        Full_time_jobs[i] = data[i]
        continue
    elif data[i]['partTime']:
        Part_time_jobs[i] = data[i]
        continue
    else:
        Neither_time_jobs[i] = data[i]

# Question 1 - Counting number of job adverts
print("There are %d job adverts in the files provided" % len(data))

# Question 2 - Count number of full-time and part-time jobs
Num_both_time_jobs = len(Both_time_jobs)
Num_full_time_jobs = len(Full_time_jobs)
Num_part_time_jobs = len(Part_time_jobs)

print("There are %d job adverts for full-time jobs, %d for part-time jobs and"
      "%d job adverts which advertise for both full-time and part-time jobs\n"
      % (Num_both_time_jobs+Num_full_time_jobs,
         Num_both_time_jobs+Num_part_time_jobs,
         Num_both_time_jobs))

# Question 3 - Plot Time-series of job adverts posted on days
Ad_dates, Ad_freq = zip(*Day_freq.items())
Ad_dates = [datetime.strptime(i, '%d/%m/%Y') for i in Ad_dates]

fig, ax1 = plt.subplots()
ax1.plot(Ad_dates, [i/1000 for i in Ad_freq])

ax1.set_title('Time-series of Number of Adverts Posted Per Day')
ax1.set_xlabel('Date')
ax1.set_ylabel('Number Posted (thousands)')

fig.autofmt_xdate()

plt.tight_layout()
plt.show()

# Question 4 - Plot Distribution of Salaries
Mean_salaries = np.array(Mean_salaries)
threshold = 3
fig, (ax1, ax2) = plt.subplots(nrows=2)


ax1.hist(Mean_salaries)
ax1.set_title('All adverts')
ax1.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('£{x:,.0f}'))
ax1.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

ax2.hist(Mean_salaries[np.where(np.abs(stats.zscore(Mean_salaries)) < threshold)])
ax2.set_title('Adverts with values %.2f std from the mean removed' % threshold)
ax2.set_xlabel('Annual Salary')
ax2.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('£{x:,.0f}'))
ax2.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

fig.suptitle('Histogram of Annual Salaries (as provided by job adverts)')
plt.tight_layout()
plt.show()

# Question 5 - Boxplot of adverts posted per weekday
weekDays = ("Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday")
Weekday_avg = {i: [] for i in weekDays}

for i in range(len(Ad_dates)):
    Weekday_avg[weekDays[Ad_dates[i].weekday()]].append(
        (Ad_dates[i], Ad_freq[i]/1000))

labels, Box_data = [*zip(*Weekday_avg.items())]
fig, ax1 = plt.subplots()

Box_data = [[i[1] for i in j] for j in Box_data]

ax1.boxplot(Box_data)
ax1.set_xticklabels(labels)
ax1.set_ylabel('Number of Ads Posted (thousands)')
ax1.set_title('Box plot showing distributions of the number adverts'
              'posted on each weekday')

plt.tight_layout()
plt.show()

# Question 2.1 - Top 5 Users by total number of job ads posted
[list({k : v for k, v in sorted(Employer_freq.items(), 
        key = lambda item: item[1])})[i][1] for i in range(5)]
    
print("\nThe 5 employers with the most ads posted are:")
print(pd.DataFrame.from_dict(Employer_freq, orient='index',
                             columns = ['Frequency']).nlargest(5, 'Frequency'))

# Question 2.2 - 5 Most common Bigrams

print("\nThe 5 most common bi-grams from the job titles are:")
print(pd.DataFrame.from_dict(Bigrams_freq, orient='index',
                             columns = ['Frequency']).nlargest(5, 'Frequency'))

# Question 2.3 - Time-series of Nurse Ads

Nurse_dates, Nurse_freq = zip(*Nurse_ads.items())
Nurse_dates = [datetime.strptime(i, '%d/%m/%Y') for i in Nurse_dates]

fig, ax1 = plt.subplots()
ax1.plot(Nurse_dates, Nurse_freq)

ax1.set_title('Time-series of Number of Nurse Adverts Posted Per Day')
ax1.set_xlabel('Date')
ax1.set_ylabel('Number Posted')

fig.autofmt_xdate()

plt.tight_layout()
plt.show()

# Question 2.4 - Wordcloud from Nurse Descriptions

Word_string = (" ").join(Nurse_descr)
wordcloud = WordCloud(width = 1000, height = 500).generate(Word_string)
plt.figure(figsize=(15,8))
plt.imshow(wordcloud)
plt.axis('off')
plt.show()

print("\n\nTime to run = %.3f(s)" % (time.time() - time_start))
