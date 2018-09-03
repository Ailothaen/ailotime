#-------------------------------------------------------------------------------
# Name:			ailotime
# Purpose:		Source code powering discord bot ailotime
#
# Author:		Ailothaen (#3768)
# Created:		july 2018
#-------------------------------------------------------------------------------

import datetime as dt
from dateutil.relativedelta import relativedelta

import pytz
import astral
import csv
import re



#--------------------------------------------------#
# Global variables                                 #
#--------------------------------------------------#

db_cities = []
db_countries = []
acceptedFormats = (
['week', '%A, %H'],
['week', '%A, %I%p'],
['week', '%A, %H:%M'],
['week', '%A, %I:%M%p'],
['time', '%H'],
['time', '%I%p'],
['time', '%H:%M'],
['time', '%I:%M%p'],
['day', '%d, %H'],
['day', '%d, %I%p'],
['day', '%d, %H:%M'],
['day', '%d, %I:%M%p'],
['complete', '%Y-%m-%d, %H'],
['complete', '%Y-%m-%d, %I%p'],
['complete', '%Y-%m-%d, %H:%M'],
['complete', '%Y-%m-%d, %I:%M%p'],
['complete', '%d/%m/%Y, %H'],
['complete', '%d/%m/%Y, %I%p'],
['complete', '%d/%m/%Y, %H:%M'],
['complete', '%d/%m/%Y, %I:%M%p']
)
link_github_base = 'https://github.com/Ailothaen/ailotime'
link_github_wiki = 'https://github.com/Ailothaen/ailotime/wiki'
link_github_issues = 'https://github.com/Ailothaen/ailotime/issues'
version = '1.0'



#--------------------------------------------------#
# Classes                                          #
#--------------------------------------------------#

class City:
	"""
	A city.
	"""
	def __init__(self, name=None, countrycode=None, latitude=None, longitude=None, altitude=None, timezone=None):
		self.name = name
		self.countrycode = countrycode
		self.latitude = latitude
		self.longitude = longitude
		self.altitude = altitude
		self.timezone_str = timezone
		
		if timezone:
			try:
				self.timezone_pytz = pytz.timezone(timezone)
			except UnknownTimeZoneError:
				raise
	
	def __repr__(self):
		return 'name={}, countrycode={}, latitude={}, longitude={}, altitude={}, timezone_str={}, timezone_pytz={}'.format(self.name, self.countrycode, self.latitude, self.longitude, self.altitude, self.timezone_str, self.timezone_pytz)

				
class Timezone:
	"""
	A timezone in the world
	"""
	def __init__(self, name=None, timezone=None):
		self.name = name
		self.timezone_str = timezone
		
		if timezone:
			try:
				self.timezone_pytz = pytz.timezone(timezone)
			except UnknownTimeZoneError:
				raise
				
	
class Output:
	"""
	The output, destined to be parsed in run.py
	"""
	def __init__(self, success=True, subtype=None, color=None, title=None, description=None, subfields=None):
		if description is None:
			description = []
		if subfields is None:
			subfields = []
		
		self.success = success
		self.subtype = subtype
		self.color = color
		self.title = title
		self.description = description
		self.subfields = subfields

	def __repr__(self):
		return 'success={}, subtype={}, color={}, title={}, description={}, subfields={}'.format(self.success, self.subtype, self.color, self.title, self.description, self.subfields)
		


#--------------------------------------------------#
# General functions                                #
#--------------------------------------------------#

def init():
	"""
	Loads the CSV files into the variables. Called only at script startup.
	"""
	global db_cities, db_countries
	
	with open('db/cities.csv', 'r', encoding='UTF-8') as file:
		reader = csv.reader(file, delimiter='\t')
		for row in reader:
			db_cities.append(row)

	with open('db/countries.csv', 'r', encoding='UTF-8') as file:
		reader = csv.reader(file, delimiter='\t')
		for row in reader:
			db_countries.append(row)

			
def errorMessage(type, **kwargs):
	"""
	Raises an error message for the user (as they are always the same). kwargs is supposed to be filled with determ... uh, various variables, depending of the message.
	"""
	# user errors
	if type == 'IncorrectPlace':
		return Output(success=False, subtype=None, color='e84118', title=':warning: Something went wrong', description=['I don\'t know the place {}. Try to write another more known city, or check whether the name is correct.'.format(kwargs['place'])], subfields=None)
	elif type == 'IncorrectInput':
		return Output(success=False, subtype=None, color='e84118', title=':warning: Something went wrong', description=['I don\'t understand at all what you wrote. Follow the guide here to properly write your command: {}'.format(link_github_wiki)], subfields=None)
	elif type == 'IncorrectTime':
		return Output(success=False, subtype=None, color='e84118', title=':warning: Something went wrong', description=['I don\'t understand the time you entered. Follow the guide here to properly write your time: {}'.format(link_github_wiki)], subfields=None)
		
	# more critical errors
	elif type == 'IncorrectData':
		return Output(success=False, subtype=None, color='e84118', title=':bangbang: Something went (really) wrong', description=['I found the place you mean, but the data I have seems to be incorrect. Please report the problem by opening an issue on {} with this info:'.format(link_github_issues, kwargs)], subfields=None)
	else:
		return Output(success=False, subtype=None, color='e84118', title=':bangbang: Something went (really) wrong', description=['... and I don\'t even know what is it. Please report the problem by opening an issue on {}.'.format(link_github_issues)], subfields=None)
	
		
def separateCountryCodes(city):
	"""
	Separates the country code from the city, if provided.
	"""
	re_countrycodes = re.match(r"^([A-Za-z0-9'/\-\s]+)\s?\(([A-Za-z]{2})\)?$", city)
	
	if re_countrycodes: # city with country code 
		re_nottuple = [] # I can't remove extra spaces with a tuple.
		re_nottuple.append(re_countrycodes.groups()[0].strip())
		re_nottuple.append(re_countrycodes.groups()[1])
		return re_nottuple
	else: # everything else
		return False
		

def strfdelta(tdelta, fmt):
	"""
	Useful timedelta function to use an ersatz of datetime.strftime()
	"""
	d = {"d": tdelta.days}
	d["H"], rem = divmod(tdelta.seconds, 3600)
	d["M"], d["S"] = divmod(rem, 60)
	return fmt.format(**d)

		
def parse_location(place, countrySpecified=None):
	"""
	Returns the correct pytz timezone object for the country, city or timezone identifier.
	(Country is specified is the place is a city and the user specified it - to avoid homonyms).
	If there are still city homonyms, the function returns the city with the most inhabitants in it.
	"""
	match = False
	place_lower = place.lower() # lowercase for comparing countries and cities
	countrySpecified = countrySpecified.upper() if countrySpecified is not None else None # always in uppercase
	
	# special cases because I guess some will get triggered by this
	if place_lower == 'new york':
		place_lower = 'new york city'
		
	wrongTimezones = {'PST': 'PST8PDT', 'PDT': 'PST8PDT', 'MST': 'MST7MDT', 'MDT': 'MST7MDT', 'CST': 'CST6CDT', 'CDT': 'CST6CDT', 'EST': 'EST5EDT', 'EDT': 'EST5EDT'}
	if place in wrongTimezones:
		place = wrongTimezones[place]
	
	# 1 : searching in cities

	for i, city in enumerate(db_cities):
		if countrySpecified == None:
			if city[1].lower() == place_lower or city[2].lower() == place_lower:
				match = True
				line = i
				break
		else:
			if(city[1].lower() == place_lower or city[2].lower() == place_lower) and (city[5] == countrySpecified):
				match = True
				line = i
				break
	
	if match:
		try:
			city = City(name=db_cities[line][1], countrycode=db_cities[line][5].lower(), latitude=db_cities[line][3], longitude=db_cities[line][4], altitude=db_cities[line][6], timezone=db_cities[line][7])
		except UnknownTimeZoneError:
			raise
		else:
			return city
		
	# 2 : searching in countries (either name or code). We get their capital if found.
	
	for i, country in enumerate(db_countries):
		if country[0].lower() == place_lower or country[2].lower() == place_lower:
			match = True
			line = i
	
	if match:
		capital = db_countries[line][3]
		countrycode = db_countries[line][0]
		
		for i, city in enumerate(db_cities):
			if city[2] == capital and city[5] == countrycode:
				line = i
				break
		
		try:
			city = City(name=db_cities[line][1], countrycode=db_cities[line][5].lower(), latitude=db_cities[line][3], longitude=db_cities[line][4], altitude=db_cities[line][6], timezone=db_cities[line][7])
		except UnknownTimeZoneError:
			raise
		else:
			return city
		
	# 3 : searching in timezone identifiers
	
	for tz in pytz.all_timezones:
		if place == tz:
			# no try/except here, as timezone exists if we're here
			return Timezone(name=tz, timezone=tz)
	
	# Definitely not found.
	raise ValueError


def parse_time(input, timezone):
	"""
	Returns a correct DateTime object for the time supplied in argument.
	Returns, as well, an appropriate format for the output formatting, depending on the "scope".
	"""
	timezone_pytz = pytz.timezone(timezone)
	now = dt.datetime.now(timezone_pytz)
	
	parsed = False
	typeOfTime = None
	
	# testing to parse with all the formats
	for format in acceptedFormats:
		try:
			# IMPORTANT : do not work directly on this date object! In most cases, the year here is equal to "1900", which cause great problems with historic timezones arrangements
			parsed = dt.datetime.strptime(input, format[1])
		except ValueError:
			pass
		else:
			typeOfTime = format[0]
			break
	
	if not parsed: # if no one is okay
		raise ValueError
	else:
		if typeOfTime == 'week':
			outputFormat = '%A %d, %H:%M'
		
			# Here we find the next occurence of day-of-week. Don't forget to look at the source current time!
			re_weekday = re.match(r"^([A-Za-z]+),", input)
			weekdayNumber = weekdayName_to_weekdayNumber(re_weekday.groups()[0])
			nextday = now + dt.timedelta(days=(weekdayNumber-now.weekday()+7)%7)
			
			dtObject = dt.datetime(year=int(nextday.strftime('%Y')), month=int(nextday.strftime('%m')), day=int(nextday.strftime('%d')), hour=int(parsed.strftime('%H')), minute=int(parsed.strftime('%M')), second=0)
			
		elif typeOfTime == 'time':
			outputFormat = '%A, %H:%M'
		
			dtObject = dt.datetime(year=int(now.strftime('%Y')), month=int(now.strftime('%m')), day=int(now.strftime('%d')), hour=int(parsed.strftime('%H')), minute=int(parsed.strftime('%M')), second=0)
			
		elif typeOfTime == 'day':
			outputFormat = '%B %d, %H:%M'
		
			 # We check if the day-of-month and time is already passed.
			dtObject_compare = dt.datetime(year=int(now.strftime('%Y')), month=int(now.strftime('%m')), day=int(parsed.strftime('%d')), hour=int(parsed.strftime('%H')), minute=int(parsed.strftime('%M')), second=0)
			dtObject_compare = timezone_pytz.localize(dtObject_compare)
			
			dtObject = dt.datetime(year=int(now.strftime('%Y')), month=int(now.strftime('%m')), day=int(parsed.strftime('%d')), hour=int(parsed.strftime('%H')), minute=int(parsed.strftime('%M')), second=0)
			
			if dtObject_compare > now:
				dtObject += relativedelta(months=+1)
			
		elif typeOfTime == 'complete':
			outputFormat = '%Y-%m-%d, %H:%M'
		
			dtObject = dt.datetime(year=int(parsed.strftime('%Y')), month=int(parsed.strftime('%m')), day=int(parsed.strftime('%d')), hour=int(parsed.strftime('%H')), minute=int(parsed.strftime('%M')), second=0)
		
		dtObject = timezone_pytz.localize(dtObject) # yeah, we can't just write tzinfo=timezone_pytz at object creation. don't ask me why
		return(dtObject, outputFormat)


def weekdayName_to_weekdayNumber(name):
	"""
	Returns 0 for Monday, 1 for Tuesday... 6 for Sunday.
	(Yeah, I know about %A and %w in strftime(), but this can't be used in the context since we don't have a complete date yet.)
	"""
	name = name.lower()
	list = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
	
	for i, day in enumerate(list):
		if name == day:
			return(i)



#--------------------------------------------------#
# a!time/from functions                            #
#--------------------------------------------------#

def parse_input_time(input):
	"""
	Parse the input and divides it into groups of exploitable data.
	"""
	re_simple = re.match(r"^([\w\s'’`-]+\s?(?:\([A-Za-z]{2}\))?)$", input)
	
	data = {}
		
	if re_simple:
		data['type'] = 'simple'
		cc_source = separateCountryCodes(re_simple.groups()[0])
		if cc_source:
			data['source'] = [cc_source[0], cc_source[1]]
		else:
			data['source'] = [re_simple.groups()[0], None]
			
		return data
		
	else:
		raise ValueError
		

def parse_input_conv(input):
	"""
	Parse the input and divides it into groups of exploitable data.
	"""
	re_conversion = re.match(r"^([A-Za-z0-9,:/\-\s]+) (?:at|in) ([\w\s'’`-]+\s?(?:\([A-Za-z]{2}\))?) (?:to|into) ((?:[\w\s'’`-]+\s?(?:\([A-Za-z]{2}\))?,?\s?)+)$", input)
	
	data = {}
	
	if re_conversion:
		data['type'] = 'conversion'
		cc_source = separateCountryCodes(re_conversion.groups()[1])
		if cc_source:
			data['source'] = [cc_source[0], cc_source[1]]
		else:
			data['source'] = [re_conversion.groups()[1], None]
	
		targets_raw = re_conversion.groups()[2]
		targets = targets_raw.split(',')
		data['targets'] = []
		data['time'] = re_conversion.groups()[0]
		
		for place in targets:
			place = place.strip()
			cc_target = separateCountryCodes(place)
			if cc_target:
				data['targets'].append([cc_target[0], cc_target[1]])
			else:
				data['targets'].append([place, None])
					
		return data
		
	else:
		raise ValueError


def colorTime(date, latitude, longitude, altitude, timezone):
	"""
	Returns a color for the "box lining", depending of the state of the sun (day, sunrise, sunset, night)
	Returns also the proper emoji to illustrate time.
	"""
	colors = {
	'day': 'ffca28',
	'sunset_civil': 'f85908',
	'sunset_nautical': '2131a6',
	'sunrise_civil': 'fd88c2',
	'sunrise_nautical': '2131a6',
	'night': '070555'
	}
	
	l = astral.Location(('Name is not necessary here', 'XX', float(latitude), float(longitude), timezone, int(altitude)))
	angle = l.solar_elevation(date)
	solarMidnight = l.solar_midnight(date)
	
	# Solar midnight can be (and usually is) after midnight. We need to set it for "the next night", as it will be the one from the previous night.
	noonToday = date.replace(hour=12, minute=0, second=0)
	if(date > noonToday):
		solarMidnight += relativedelta(days=+1)
	
	if angle > 2:
		return(colors['day'], ':sun_with_face:') # day
	elif angle > -6:
		if date < solarMidnight:
			return(colors['sunset_civil'], ':sun_with_face: :arrow_down:') # civil sunset
		else:
			return(colors['sunrise_civil'], ':sun_with_face: :arrow_up:') # civil sunrise
	elif angle > -12:
		if date < solarMidnight:
			return(colors['sunset_nautical'], ':last_quarter_moon_with_face: :arrow_up:') # nautical sunset
		else:
			return(colors['sunrise_nautical'], ':last_quarter_moon_with_face: :arrow_down:') # nautical sunrise
	else:
		return(colors['night'], ':last_quarter_moon_with_face:') # night

	

#--------------------------------------------------#
# a!sun/sundetails functions                       #
#--------------------------------------------------#

def parse_input_sun(input):
	"""
	Parse the input and divides it into groups of exploitable data.
	"""
	# Simple case
	re_now = re.match(r"^([\w\s'’`-]+\s?(?:\([A-Za-z]{2}\))?)$", input)
	
	# We also provide a date
	re_other = re.match(r"^([A-Za-z0-9,:/\-\s]+) (?:at|in) ([\w\s'’`-]+\s?(?:\([A-Za-z]{2}\))?)$", input)
	
	data = {}
		
	if re_other:
		data['type'] = 'other'
		data['time'] = re_other.groups()[0]
		cc_source = separateCountryCodes(re_other.groups()[1])
		
		if cc_source:
			data['source'] = [cc_source[0], cc_source[1]]
		else:
			data['source'] = [re_other.groups()[1], None]
			
		return data
	
	elif re_now: # re_now after re_other, otherwises it always matches re_now if re_other matches. I am too lazy to correct that
		data['type'] = 'now'
		cc_source = separateCountryCodes(re_now.groups()[0])
		if cc_source:
			data['source'] = [cc_source[0], cc_source[1]]
		else:
			data['source'] = [re_now.groups()[0], None]
			
		return data
		
	else:
		raise ValueError
		

def sunrise_sunset(date, latitude, longitude, altitude, types):
	"""
	Calculates sunrise and sunsets on a location depending of a date.
	"""
	l = astral.Location(('NotNecessaryHere', 'XX', float(latitude), float(longitude), str(date.tzinfo), int(altitude)))
	
	sun = {}
	
	if 'ra' in types:
		l.solar_depression = 'astronomical'
		try:
			sun['ra'] = l.dawn(date=date)
		except astral.AstralError:
			sun['ra'] = False
	
	if 'rn' in types:
		l.solar_depression = 'nautical'
		try:
			sun['rn'] = l.dawn(date=date)
		except astral.AstralError:
			sun['rn'] = False
			
	if 'rc' in types:
		l.solar_depression = 'civil'
		try:
			sun['rc'] = l.dawn(date=date)
		except astral.AstralError:
			sun['rc'] = False
			
	if 'r' in types:
		try:
			sun['r'] = l.sunrise(date=date)
		except astral.AstralError:
			sun['r'] = False
			
	if 'sol_n' in types:
		try:
			sun['sol_n'] = l.solar_noon(date=date)
		except astral.AstralError:
			sun['sol_n'] = False
			
	if 'sol_m' in types:
		try:
			sun['sol_m'] = l.solar_midnight(date=date)
		except astral.AstralError:
			sun['sol_m'] = False
			
	if 's' in types:
		try:
			sun['s'] = l.sunset(date=date)
		except astral.AstralError:
			sun['s'] = False	
	
	if 'sc' in types:
		l.solar_depression = 'civil'
		try:
			sun['sc'] = l.dusk(date=date)
		except astral.AstralError:
			sun['sc'] = False
			
	if 'sn' in types:
		l.solar_depression = 'nautical'
		try:
			sun['sn'] = l.dusk(date=date)
		except astral.AstralError:
			sun['sn'] = False
			
	if 'sa' in types:
		l.solar_depression = 'astronomical'
		try:
			sun['sa'] = l.dusk(date=date)
		except astral.AstralError:
			sun['sa'] = False
			
	if 'day' or 'night' in types:
		try:
			day = l.daylight(date=date, local=True)
			delta_day = day[1] - day[0]
			delta_night = dt.timedelta(hours=24) - delta_day
			sun['day'] = strfdelta(delta_day, '{H} h {M} min')
			sun['night'] = strfdelta(delta_night, '{H} h {M} min')
		except astral.AstralError as e:
			if l.solar_elevation(date) > 0:
				sun['day'] = '24 h 00 min'
				sun['night'] = '0 h 00 min'
			else:
				sun['day'] = '0 h 00 min'
				sun['night'] = '24 h 00 min'
		
	return sun



#--------------------------------------------------#
# Command handlers                                 #
#--------------------------------------------------#

def command_time(input):
	"""
	"time" command handler
	example: a!time Aix-en-Provence (FR)
	"""
	output = Output()
	output.subtype = 'simple'
	
	# trying to understand the command entered
	try:
		parsed = parse_input_time(input)
	except ValueError: # total mess in command
		return errorMessage('IncorrectInput')
	
	# trying to find source location
	try:
		source = parse_location(*parsed['source'])
	except ValueError: # location not found
		return errorMessage('IncorrectPlace', place=parsed['source'][0])
	except UnknownTimeZoneError: # location found, but incorrect timezone
		return errorMessage('IncorrectData')
	
	# converting
	timeAtSource = dt.datetime.now(source.timezone_pytz)
	
	if isinstance(source, City):
		output.title = 'Current time at '+source.name+' :flag_'+source.countrycode+': :'
		# setting a nice color depending of day/night :)
		output.color, emoji = colorTime(timeAtSource, source.latitude, source.longitude, source.altitude, source.timezone_str)
		output.description.append(emoji+' '+timeAtSource.strftime('%A, %H:%M'))
		
	elif isinstance(source, Timezone):
		output.title = 'Current time in timezone '+source.name+':'
		output.description.append(timeAtSource.strftime('%A, %H:%M'))
		output.color = '808080'
	
	return output
	

def command_conv(input):
	"""
	"conv" command handler
	example: a!conv 15:30 at Aix-en-Provence (FR) to Reykjavik, PST
	"""
	output = Output()
	output.subtype = 'conversion'
	output.color = '808080'
	
	# trying to understand the command entered
	try:
		parsed = parse_input_conv(input)
	except ValueError: # total mess in command
		return errorMessage('IncorrectInput')
	
	# trying to find source location
	try:
		source = parse_location(*parsed['source'])
	except ValueError: # location not found
		return errorMessage('IncorrectPlace', place=parsed['source'][0])
	except UnknownTimeZoneError: # location found, but incorrect timezone
		return errorMessage('IncorrectData')
	
	# trying to find all targets locations
	for i, place in enumerate(parsed['targets']):
		try:
			parsed['targets'][i] = parse_location(*place)
		except ValueError: # same
			return errorMessage('IncorrectPlace', place=parsed['targets'][i][0])
	
	# trying to parse time
	try:
		parsed['time'], outputFormat = parse_time(parsed['time'], source.timezone_str)
	except ValueError:
		return errorMessage('IncorrectTime')
	
	# here we are
	timeAtSource = parsed['time']
	
	if isinstance(source, City):
		output.title = timeAtSource.strftime(outputFormat)+' at '+source.name+' :flag_'+source.countrycode+': is:'
	elif isinstance(source, Timezone):
		output.title = timeAtSource.strftime(outputFormat)+' '+source.name+' is:'
	
	for place in parsed['targets']:
		# converting for every target
		timeAtTarget = timeAtSource.astimezone(place.timezone_pytz)
		
		if isinstance(place, City):
			output.description.append(timeAtTarget.strftime(outputFormat)+' at '+place.name+' :flag_'+place.countrycode+':')
		elif isinstance(place, Timezone):
			output.description.append(timeAtTarget.strftime(outputFormat)+' '+place.name)
	
	return output
	

def command_sun(input, detailed=False):
	"""
	"time" command handler
	example: a!sun Reykjavík
	"""
	output = Output()
	output.color = '808080'
	
	try:
		parsed = parse_input_sun(input)
	except ValueError: # total mess in command
		return errorMessage('IncorrectInput')
		
	try:
		source = parse_location(*parsed['source'])
	except ValueError: # location not found
		return errorMessage('IncorrectPlace', place=parsed['source'][0])
	
	if parsed['type'] == 'other':
		# trying to parse time
		try:
			timeAtSource = parse_time(parsed['time'], source.timezone_str)[0] # we don't care about outputFormat
		except ValueError:
			return errorMessage('IncorrectTime')
	else:
		timeAtSource = dt.datetime.now(source.timezone_pytz)
			
	output.title = 'Sun information at '+source.name+' :flag_'+source.countrycode+':'
	
	# here we are
	if detailed:
		sun = sunrise_sunset(timeAtSource, source.latitude, source.longitude, source.altitude, ('ra', 'rn', 'rc', 'r', 's', 'sc', 'sn', 'sa', 'sol_n', 'sol_m', 'day'))
		
		output.description.append('Day length: '+sun['day'])
		output.description.append('Night length: '+sun['night'])
		output.description.append('') # could have used \n but prefer that for readability issues
		
		output.description.append('Astronomical dawn: '+('not today' if not sun['ra'] else sun['ra'].strftime('%H:%M')))
		output.description.append('Nautical dawn: '+('not today' if not sun['rn'] else sun['rn'].strftime('%H:%M')))
		output.description.append('Civil dawn: '+('not today' if not sun['rc'] else sun['rc'].strftime('%H:%M')))
		output.description.append('Sunrise: '+('not today' if not sun['r'] else sun['r'].strftime('%H:%M')))
		output.description.append('')
		
		output.description.append('Sunset: '+('not today' if not sun['s'] else sun['s'].strftime('%H:%M')))
		output.description.append('Civil dusk: '+('not today' if not sun['sc'] else sun['sc'].strftime('%H:%M')))
		output.description.append('Nautical dusk: '+('not today' if not sun['sn'] else sun['sn'].strftime('%H:%M')))
		output.description.append('Astronomical dusk: '+('not today' if not sun['sa'] else sun['sa'].strftime('%H:%M')))
		output.description.append('')
		
		output.description.append('Solar noon: '+sun['sol_n'].strftime('%H:%M'))
		output.description.append('Solar midnight: '+sun['sol_m'].strftime('%H:%M'))
		output.description.append('')
		
		output.description.append('Information about these values can be found here: https://en.wikipedia.org/wiki/Twilight')
	else:
		sun = sunrise_sunset(timeAtSource, source.latitude, source.longitude, source.altitude, ('rn', 'r', 's', 'sn', 'day'))
		
		output.description.append('Day length: '+sun['day'])
		output.description.append('')
		
		output.description.append('Dawn: '+('not today' if not sun['rn'] else sun['rn'].strftime('%H:%M')))
		output.description.append('Sunrise: '+('not today' if not sun['r'] else sun['r'].strftime('%H:%M')))
		output.description.append('Sunset: '+('not today' if not sun['s'] else sun['s'].strftime('%H:%M')))
		output.description.append('Dusk: '+('not today' if not sun['sn'] else sun['sn'].strftime('%H:%M')))
		
	return output
	

def command_credits(input, detailed=False):
	"""
	"help" command handler
	example: a!help time
	"""
	output = Output()
	output.color = '808080'
	
	output.title = input
	return output
	

#--------------------------------------------------#
# Initializer                                      #
#--------------------------------------------------#

# Loads the files to be able to do everything.
init()

# For tests. Only executed if ailotime.py is directly executed.
if __name__ == '__main__':
	input = input('=> ')
	print(command_sun(input, detailed=True))
