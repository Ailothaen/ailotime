import csv

"""
This file is meant to be used manually when generating the database CSV files.
It takes the data from the files "cities15000.txt" and "countryInfo.txt" (see http://download.geonames.org/export/dump/), removes useless info and sort them in the meant order. Then it writes the new data to cities.csv and countries.csv.
"""

cities = []
countries = []

processed_cities = []
processed_countries = []


with open('./cities15000.txt', 'r', encoding='UTF-8') as file:
	reader = csv.reader(file, delimiter='\t')
	for row in reader:
		cities.append(row)
		
with open('./countryInfo.txt', 'r', encoding='UTF-8') as file:
	reader = csv.reader(file, delimiter='\t')
	for row in reader:
		countries.append(row)
		
# sort cities by population
cities = sorted(cities, key=lambda x: int(x[14]), reverse=True)

# removing useless data from cities
for item in cities:
	del item[18] # last update
	del item[15] # elevation (we use "dem" ([16]) instead, as elevation is rarely provided)
	del item[14] # population (we don't need it anymore)
	del item[13] # admin4 code
	del item[12] # admin3 code
	del item[11] # admin2 code
	del item[10] # admin1 code
	del item[9] # alternate country code
	del item[7] # feature code
	del item[6] # feature class
	del item[3] # alternate names

for item in countries:
	del item[18] # equivalent fips code
	del item[17] # neighbors countries
	del item[15] # language
	del item[14] # postal code regex
	del item[13] # postal code format
	del item[12] # phone
	del item[11] # currency name
	del item[10] # currency code
	del item[9] # tld
	del item[8] # continent
	del item[7] # population
	del item[6] # area
	del item[3] # fips
	del item[2] # ISO-Numeric
	
with open('./cities.csv', 'w', encoding='UTF-8', newline='') as file:
	writer = csv.writer(file, delimiter='\t')
	writer.writerows(cities)

with open('./countries.csv', 'w', encoding='UTF-8', newline='') as file:
	writer = csv.writer(file, delimiter='\t')
	writer.writerows(countries)
