# bot.py
import os
import discord
from discord.ext import commands
import psycopg2


#from dotenv import load_dotenv
#load_dotenv()

bot_settings = {}
db_conn = None

bot = commands.Bot(command_prefix='!')
default_notif_message_format = 'Yo, [ROLE]. Newb alert: [NEWBIE] joined!\nBetter make sure they get the right nickname and role set up'


class bot_setting:
	guild_id = 0
	guild_name = None
	notif_role_id = None
	notif_channel_id = None
	notif_message_format = None

	def __init__(self, guild_id, guild_name, notif_role_id, notif_channel_id, notif_message_format):
		self.guild_id = guild_id
		self.guild_name = guild_name
		self.notif_role_id = notif_role_id
		self.notif_channel_id = notif_channel_id
		self.notif_message_format = notif_message_format

	def toString(self):
		return '[ guild_id[{0}],guild_name[{1}],notif_role_id[{2}],notif_channel_id[{3}],notif_message_format[{4}] ]'.format(self.guild_id,self.guild_name,self.notif_role_id,self.notif_channel_id,self.notif_message_format)

################################################################################
## DB methods
##
def open_db_connection():
	global db_conn
	try:
		if db_conn is None or db_conn.closed != 0:
			DATABASE_URL = os.environ['DATABASE_URL'] #os.getenv('DATABASE_URL') #
			db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
	except:
		print('there was a problem opening the connection')
		raise

def close_db_connection():
	try:
		if db_conn.closed == 0:
			db_conn.close()
	except:
		print('there was a problem closing the connection')
		raise

def execute_query(sql):
	results = None
	cur = None
	try:
		open_db_connection()
		cur = db_conn.cursor()
		cur.execute(sql)
		results = cur.fetchall()
	except:
		print(f'failed when running sql:\n{sql}')
		raise
	finally:
		close_db_connection()

	return results

def execute_non_query(sql):
	# print(f'executing:\n{sql}')
	try:
		open_db_connection()
		cur = db_conn.cursor()
		cur.execute(sql)
		db_conn.commit()
	except Exception as e:
		print(f'failed when running non-query:\n{sql}')
		print(e)
		raise
	finally:
		close_db_connection()

def query_for_bot_configs(guild_id = None):
	print('getting bot settings from the DB')

	settings = {}
	query = '''select guild_id,
                      guild_name,
                      notif_role_id,
                      notif_channel_id,
                      notif_message_format
                 from bot_configs'''
	if guild_id is not None:
		query = query + ' where guild_id = ' + guild_id

	rows = execute_query(query)
	print(f'found {len(rows)} rows')
	
	for row in rows:
		settings[row[0]]=bot_setting(row[0],row[1],row[2],row[3],row[4])
		# print(f'found setting for guild id[{settings[row[0]].guild_id}]: {settings[row[0]].toString()}')
		print(f'found setting for guild id[{settings[row[0]].guild_id}] name[{settings[row[0]].guild_name}]')
	return settings

def insert_bot_config(setting:bot_setting):
	query = '''INSERT INTO bot_configs (
                 guild_id,
                 guild_name,
                 notif_role_id,
                 notif_channel_id,
                 notif_message_format
               ) VALUES (
                 {0},
                 '{1}',
                 {2},
                 {3},
                 '{4}')'''.format(setting.guild_id, setting.guild_name.replace('\'', '\'\'') if setting.guild_name is not None else 'NULL', setting.notif_role_id if setting.notif_role_id is not None else 'NULL', setting.notif_channel_id if setting.notif_channel_id is not None else 'NULL', setting.notif_message_format.replace('\'', '\'\'') if setting.notif_message_format is not None else 'NULL')

	try:
		rows = execute_non_query(query)
		return True
	except:
		return False
		
def update_bot_config(setting:bot_setting):
	query = '''UPDATE bot_configs
                  SET guild_name = '{1}',
                      notif_role_id = {2},
                      notif_channel_id = {3},
                      notif_message_format = '{4}'
                WHERE guild_id = {0}'''.format(setting.guild_id, setting.guild_name.replace('\'', '\'\'') if setting.guild_name is not None else 'NULL', setting.notif_role_id if setting.notif_role_id is not None else 'NULL', setting.notif_channel_id if setting.notif_channel_id is not None else 'NULL', setting.notif_message_format.replace('\'', '\'\'') if setting.notif_message_format is not None else 'NULL')

	try:
		rows = execute_non_query(query)
		return True
	except:
		return False
##
##
################################################################################



def setup_check():
	global bot_settings
	
	#check if table exists on DB
	rows = execute_query('select table_name, table_schema from information_schema.tables where table_schema=\'public\'')
	found_table = False
	for row in rows:
		if row[0] == 'bot_configs':
			found_table = True
			break

	# if table doesn't exist, add it
	if found_table == False:
		execute_non_query('''create table bot_configs (
                               guild_id BIGINT PRIMARY KEY NOT NULL,
                               guild_name VARCHAR(100),
                               notif_role_id BIGINT,
                               notif_channel_id BIGINT,
                               notif_message_format VARCHAR(1000)
                             );''')
		print('created the bot_configs table')

	bot_settings = query_for_bot_configs()
	for guild in bot.guilds:
		print(f'running on server: {guild.name} {guild.id}')
		if guild.id not in bot_settings:
			bot_settings[guild.id] = bot_setting(guild.id, guild.name, None, guild.system_channel, default_notif_message_format)
			insert_bot_config(bot_settings[guild.id])




################################################################################
## Help display functions
##
def set_notif_role_help():
	message = 'mofo_set_notif_role role\n'
	message = message + '+ This command sets the role to notify when a new member joins the server. '
	message = message + 'It\'s used to replace the [ROLE] key phrase in the notification message.'
	message = message + '\n- Pass \'help\' or \'?\' or no argument to the command to show this help text.'
	return message
	
def set_notif_channel_help():
	message = 'mofo_set_notif_channel channel\n'
	message = message + '+ This command sets the channel to post in when a new member joins the server. '
	message = message + 'If no channel is set, the default system notification channel will be used.'
	message = message + '\n- Pass \'help\' or \'?\' or no argument to the command to show this help text.'
	return message
	
def set_notif_message_help():
	message = 'mofo_set_notif_message message\n'
	message = message + '+ This command sets the message to send when a new member joins the server.\n'
	message = message + '+ The key phrases [ROLE] and [NEWBIE] in the message will be replaced with '
	message = message + 'the role set by the mofo_set_notif_role command and the new member respectively '
	message = message + 'when the message is sent.'
	message = message + '\n- Pass \'help\' or \'?\' or no argument to the command to show this help text.'
	return message
	
def get_notif_role_help():
	message = 'mofo_get_notif_role\n'
	message = message + '+ This command prints the role to notify when a new member joins the server.'
	return message

def get_notif_channel_help():
	message = 'mofo_get_notif_channel\n'
	message = message + '+ This command prints the channel to post in when a new member joins the server.'
	return message

def get_notif_message_help():
	message = 'mofo_get_notif_message\n'
	message = message + '+ This command prints the message to send when a new member joins the server.\n'
	message = message + '+ The key phrases [ROLE] and [NEWBIE] in the message will be replaced with '
	message = message + 'the role set by the mofo_set_notif_role command and the new member respectively '
	message = message + 'when the message is sent.'
	return message

def get_all_settings():
	message = 'mofo_get_all_settings\n'
	message = message + '+ This command prints the current role, channel, and message to use when a new member '
	message = message + 'joins the server.\n'
	message = message + '+ This is the equivalent of running the mofo_get_notif_role, mofo_get_notif_channel, '
	message = message + 'and mofo_get_notif_message commands back-to-back.'
	return message

async def print_help(channel:discord.TextChannel, message, premessage = None):
	if premessage is None:
		await channel.send(f'```diff\n{message}```')
	else:
		await channel.send(f'{premessage}\n```diff\n{message}```')
##
##
################################################################################



################################################################################
## Bot commands
##
@bot.command(pass_context=True)
async def mofo_set_notif_role(ctx, arg=None):
	global bot_settings
	if arg is None or (type(arg) != discord.Role and (arg.lower() == 'help' or arg.lower() == '?' or arg.lower() == '-help')):
		await print_help(ctx.channel, set_notif_role_help())
		return
	
	setting = bot_settings[ctx.guild.id]
	
	
	if setting.notif_role_id != arg.id:
		setting.notif_role_id = arg.id
		update_bot_config(setting)
		
	await ctx.channel.send(f'Notification role updated')
	
@bot.command(pass_context=True)
async def mofo_set_notif_channel(ctx, arg=None):
	global bot_settings
	if arg is None or (type(arg) != discord.TextChannel and (arg.lower() == 'help' or arg.lower() == '?' or arg.lower() == '-help')):
		await print_help(ctx.channel, set_notif_channel_help())
		return
	
	setting = bot_settings[ctx.guild.id]
	
	if setting.notif_channel_id != arg.id:
		setting.notif_channel_id = arg.id
		update_bot_config(setting)
		
	await ctx.channel.send(f'Notification channel updated')
	
@bot.command(pass_context=True)
async def mofo_set_notif_message(ctx, *, message):
	global bot_settings
	if message is None or message == '' or message.lower() == '-help' or message.lower() == 'help':
		await print_help(ctx.channel, set_notif_message_help())
		return

	setting = bot_settings[ctx.guild.id]
	
	if setting.notif_message_format != message:
		setting.notif_message_format = message
		update_bot_config(setting)
		
	await ctx.channel.send(f'Notification message updated')

@bot.command(pass_context=True)
async def mofo_get_notif_role(ctx):
	setting = bot_settings[ctx.guild.id]
	if setting.notif_role_id is not None:
		role = ctx.guild.get_role(setting.notif_role_id)
		await ctx.channel.send(f'The role to mention when a new member joins is {role.mention}')
	else:
		await ctx.channel.send('There is no saved role to mention when a new member joins. use the _mofo\_set\_notif\_role_ command to set it')
		
@bot.command(pass_context=True)
async def mofo_get_notif_channel(ctx):
	setting = bot_settings[ctx.guild.id]
	if setting.notif_channel_id is not None:
		channel = ctx.guild.get_channel(setting.notif_channel_id)
		await ctx.channel.send(f'The channel to post in when a new member joins is {channel.mention}')
	else:
		await ctx.channel.send('There is no saved channel to mention when a new member joins. use the _mofo\_set\_notif\_channel_ command to set it')
		
@bot.command(pass_context=True)
async def mofo_get_notif_message(ctx):
	setting = bot_settings[ctx.guild.id]
	if setting.notif_message_format is not None:
		await ctx.channel.send(f'The message to post when a new member joins is:\n{setting.notif_message_format}')
	else:
		await ctx.channel.send('There is no saved message to post when a new member joins. use the _mofo\_set\_notif\_message_ command to set it')
		
@bot.command(pass_context=True)
async def mofo_get_all_settings(ctx):
	setting = bot_settings[ctx.guild.id]
	message = 'Handy Dandy Helper Mofo settings:\n\tRole: '
	if setting.notif_role_id is not None:
		role = ctx.guild.get_role(setting.notif_role_id)
		message = message + role.mention
	else:
		message = message + 'None. [use the _mofo\_set\_notif\_role_ command to set it]'
	
	message = message + '\n\tChannel: '
	
	if setting.notif_channel_id is not None:
		channel = ctx.guild.get_channel(setting.notif_channel_id)
		message = message + channel.mention
	else:
		message = message + 'None. [use the _mofo\_set\_notif\_channel_ command to set it]'
	
	message = message + '\n\tMessage: '

	if setting.notif_message_format is not None:
		message = message + setting.notif_message_format
	else:
		message = message + 'None. [use the _mofo\_set\_notif\_message_ command to set it]'
	
	await ctx.channel.send(message)
	
@bot.command(pass_context=True)
async def mofo_help(ctx):
	help_message = set_notif_role_help() + '\n\n'
	help_message = help_message + set_notif_channel_help() + '\n\n'
	help_message = help_message + set_notif_message_help() + '\n\n'
	help_message = help_message + get_notif_role_help() + '\n\n'
	help_message = help_message + get_notif_channel_help() + '\n\n'
	help_message = help_message + get_notif_message_help() + '\n\n'
	help_message = help_message + get_all_settings()

	await print_help(ctx.channel, help_message, '**Handy Dandy Helper Mofo commands:**')

@bot.command(pass_context=True)
async def mofo_commands(ctx):
	message = '**mofo_set_notif_role** _role_ - sets the role to notify when new user joins\n'
	message = message + '**mofo_set_notif_channel** _channel_ - sets the channel to post in when new user joins\n'
	message = message + '**mofo_set_notif_message** _message_ - sets the message to send when new user joins\n'
	message = message + '**mofo_get_notif_role** - displays the role to notify\n'
	message = message + '**mofo_get_notif_channel** - displays the channel to post in\n'
	message = message + '**mofo_get_notif_message** - displays the message to send\n'
	message = message + '**mofo_get_all_settings** - displays the result of the other three mofo\_get\_ commands\n'
	message = message + '**mofo_help** - displays more detailed info on the mofo\_ commands\n'
	message = message + '**boop** _user_(optional) - boops the user passed, or the sender of the command if no used passed\n'
	message = message + '**bonk** _user_(optional) - bonks the user passed or the sender of the command if no used passed\n'

	await ctx.channel.send(message)
##
##
################################################################################



################################################################################
## silly commands
##
@bot.command(pass_context=True)
async def boop(ctx, *args):
	if len(args) == 0:
		await ctx.channel.send(f'**BOOP, {ctx.message.author.mention}!**')
	elif len(args) == 1 and type(args[0]) is discord.Member:
		await ctx.channel.send(f'**BOOP, {args[0].mention}!**')
	else:
		msg = ' '.join(args)
		await ctx.channel.send(f'**BOOP, {msg}!**')


@bot.command(pass_context=True)
async def bonk(ctx, arg:discord.Member=None):
	if arg is None:
		await ctx.channel.send(f'**BONK, {ctx.message.author.mention}!**')
	else:
		await ctx.channel.send(f'**BONK, {arg.mention}!**')

##
##
################################################################################


	
################################################################################
## on_member_join
##  notify the appropriate channel and role there's a new memeber
##
@bot.event
async def on_member_join(ctx):
	setting = bot_settings[ctx.guild.id]

	notif_channel = None
	if setting.notif_channel_id is None:
		notif_channel = ctx.guild.system_channel
	else:
		notif_channel = ctx.guild.get_channel(setting.notif_channel_id)

	notif_role = None
	if setting.notif_role_id is not None:
		notif_role = ctx.guild.get_role(setting.notif_role_id)

	if notif_role is not None:
		notif_message = setting.notif_message_format

		notif_message = notif_message.replace('[ROLE]', notif_role.mention)
		notif_message = notif_message.replace('[NEWBIE]', ctx.mention)

		await notif_channel.send(notif_message)
	else:
		await notif_channel.send(f'Welcome to the mayhem, {ctx.mention}!')
		

@bot.event
async def on_ready():
	print(f'{bot.user} has connected to Discord!')

	global bot_settings

	setup_check()


token = os.getenv('TOKEN') #os.environ['TOKEN'] #
bot.run(token)


#######################################################
## TODO
## - store all unhandled newbs in DB
## - cmd: set nickname for newb
## - - make it remove the newb from teh db list
## - cmd: get list of unhandled newbs
## - cmd: remove newb from list
## - cmd: purge newb list


