#-------------------------------------------------------------------------------
# Name:			ailotime
# Purpose:		Source code powering discord bot ailotime
#
# Author:		Ailothaen (#3768)
# Created:		july 2018
#-------------------------------------------------------------------------------

import discord
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
import platform

import ailotime


client = Bot(description="ailotime – a useful bot for timezones and daylight stuff", command_prefix="a!", pm_help=False)
token = 'YOUR TOKEN HERE'

# this command is awfully documented for now (like most of discord.py, actually...), so let's do a custom command for now.
client.remove_command('help')

# prevents non-existant commands to be reported as exceptions
@client.event
async def on_command_error(error, ctx):
	if isinstance(error, commands.CommandNotFound):
		pass


@client.event
async def on_ready():
	"""
	What to do at startup.
	"""
	print('--------')
	print('ailotime is ready!')
	print('Logged in as '+client.user.name+' (ID:'+client.user.id+') | Connected to '+str(len(client.servers))+' servers | Connected to '+str(len(set(client.get_all_members())))+' users')
	print('Current discord.py version: {} | Current python Version: {} | Current ailotime version: {}'.format(discord.__version__, platform.python_version(), ailotime.version))
	print('Github: {}'.format(ailotime.link_github_base))
	print('--------')


@client.command()
async def time(*, input=''):
	"""
	Tells the current time for a city, a country or a timezone.
	
	Examples:
	`a!time Athens` will tell the current time at Athens.
	`a!time China` will tell the current time at Beijing (capital of China)
	`a!time CET` will tell the current time in the timezone CET (Central European Time)
	
	For more info, check the wiki at github.com/Ailothaen/ailotime/wiki
	"""
	output = ailotime.command_time(input)
	embed_answer = discord.Embed(title=output.title, description='\n'.join(output.description), color=int(output.color, 16))
	
	await client.say(embed=embed_answer)
	

@client.command()
async def conv(*, input=''):
	"""
	Convert a date or a time set in a timezone into another(s) timezone(s).
	
	Examples:
	`a!conv 15 at Marseille to Helsinki` converts 15:00 in Marseille time to Helsinki time
	`a!time 16,1am at Moscow to London` converts 1:00 (or 1 AM) on the 16th day-of-month in Moscow time to London time
	`a!time 11:03 in CET to PST` converts 11:03 in Central European time to Pacific Standard Time
	`a!time 23/02,21:00 in Reykjavík(IS) to Los Angeles, New York City, Moscow, JP` converts 21:00 on the February 23 in Reyjavík time to Los Angeles, New York City, Moscow and Tokyo time
	
	For more info, check the wiki at github.com/Ailothaen/ailotime/wiki
	"""
	output = ailotime.command_conv(input)
	embed_answer = discord.Embed(title=output.title, description='\n'.join(output.description), color=int(output.color, 16))
	
	await client.say(embed=embed_answer)

	
@client.command()
async def sun(*, input=''):
	"""
	Displays some info about the sun in some city, like sunset or sunrise for that day.
	
	Examples:
	`a!sun Berlin` displays sun info about Berlin.
	`a!sun SK` displays sun info about Bratislava (capital of Slovakia, or SK).
	
	For more info, check the wiki at github.com/Ailothaen/ailotime/wiki
	"""
	output = ailotime.command_sun(input, detailed=False)
	embed_answer = discord.Embed(title=output.title, description='\n'.join(output.description), color=int(output.color, 16))
	
	await client.say(embed=embed_answer)

	
@client.command()
async def sundetails(*, input=''):
	"""
	Same as a!sun but more detailed.
	
	Examples:
	`a!sundetails` India displays detailed sun info about New Delhi (capital of India).
	`a!sundetails` Lima displays detailed sun info about Lima.
	
	For more info, check the wiki at github.com/Ailothaen/ailotime/wiki
	"""
	output = ailotime.command_sun(input, detailed=True)
	embed_answer = discord.Embed(title=output.title, description='\n'.join(output.description), color=int(output.color, 16))
	
	await client.say(embed=embed_answer)


@client.command()
async def help():
	"""
	Temporary "polyfill" help command.
	"""
	output = ailotime.Output(success=True, subtype=None, color='00a7bf', title=':information_source: Help / Info', description=['ailotime – a useful bot for timezones and daylight stuff', '', 'Made by Ailothaen#3768', 'Icon drawn by Applestream#1108', '', 'If you have any questions about the bot, or want to find help about the commands, check the Github here: {}'.format(ailotime.link_github_base)], subfields=None)
	
	embed_answer = discord.Embed(title=output.title, description='\n'.join(output.description), color=int(output.color, 16))
	
	await client.say(embed=embed_answer)

# Let's go
client.run(token)
