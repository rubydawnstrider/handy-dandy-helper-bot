# bot.py
import discord
import os
from discord.ext import commands
import json

#from dotenv import load_dotenv
#load_dotenv()

bot_settings = {}

json_path = 'bot_data.json'

bot = commands.Bot(command_prefix='!')
default_join_notif = 'Yo, [ROLE]. Newb alert: [NEWBIE] joined!\nBetter make sure they get the right nickname and role set up'

##################################################################################################
##################################################################################################
## settings
##  displays the current settings for the bot
##
@bot.command(pass_context=True)
async def settings(ctx):
    bot_set = bot_settings[str(ctx.guild.id)]
    printOut = 'HandyDandyHelperMofo settings\n  repeat channel: '
    if bot_set['repeat_channel'] is not None:
        printOut = printOut + bot_set['repeat_channel']
    printOut = printOut + '\n  repeat role: '
    if bot_set['repeat_role'] is not None:
        printOut = printOut + bot_set['repeat_role']
    printOut = printOut + '\n  notification message: '
    if bot_set['join_notif'] is not None:
        printOut = printOut + bot_set['join_notif']
    else:
        printOut = printOut + default_join_notif
        
    await ctx.channel.send(printOut)


##################################################################################################
##################################################################################################
## set_join_notif
##  sets the message to display when a new member joins.
##  assumes [ROLE] will be replaced with the role to @ and [NEWBIE] will be the new member
##  if nothing, '?' or '-help' are passed, will display a help text on the command cuz this one is trickier
##
@bot.command(pass_context=True)
async def set_join_notif(ctx, *, arg):
    if arg is None or arg == '?' or arg.lower() == '-help':
        await ctx.channel.send(' **!set_notif_join arg**:\npass the message you want to display on the !repeat\_channel channel when a new member joins the server.\nTo have the message mention the !repeat\_role role, put the string _[ROLE]_ in the message.\nLikewise use _[NEWBIE]_ for the new member.')
        return

    #server should have been added in setup so we'll assume its available to update
    global bot_settings
    guild = bot_settings[str(ctx.guild.id)]
    if arg != guild['join_notif']:
        guild['join_notif'] = arg
        with open(json_path,'w') as json_file:
            json.dump(bot_settings, json_file)

    await ctx.channel.send(f'notification messages saved as {arg}')

 


##################################################################################################
##################################################################################################
## set_repeat_ch
##  sets the channel to post in when a new member joins. bot must has write access to the channel
##
@bot.command(pass_context=True)
async def set_repeat_ch(ctx, arg:discord.TextChannel):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    if arg is None:
        await ctx.channel.send('huh? you need to provide a channel')
        return

    #server should have been added in setup so we'll assume its available to update
    global bot_settings
    guild = bot_settings[str(ctx.guild.id)]
    if arg.id != guild['repeat_channel']:
        guild['repeat_channel'] = arg.id
        with open(json_path,'w') as json_file:
            json.dump(bot_settings, json_file)

    await ctx.channel.send(f'repeat channel saved as {arg.mention}')


##################################################################################################
##################################################################################################
## set_repeat_role
##  sets the role to @ when a new member joins
##
@bot.command(pass_context=True)
async def set_repeat_role(ctx, arg:discord.Role):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    if arg is None:
        await ctx.channel.send('huh? you need to provide a role')
        return

    global bot_settings
    guild = bot_settings[str(ctx.guild.id)]
    if arg.id != guild['repeat_role']:
        guild['repeat_role'] = arg.id
        with open(json_path,'w') as json_file:
            json.dump(bot_settings, json_file)
    await ctx.channel.send(f'repeat role saved as {arg.mention}')

    

##################################################################################################
##################################################################################################
## repeat_ch
##  displays the current channel to post in when a new member joins
##
@bot.command(pass_context=True)
async def repeat_ch(ctx):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return

    global bot_settings
    
    guild = bot_settings[str(ctx.guild.id)]
    if guild is None:
        await ctx.channel.send('no repeat channel is saved')
        return

    channel = ctx.guild.get_channel(guild['repeat_channel'])
    if channel is not None:
        await ctx.channel.send(f'repeat channel is currently {channel.mention}')
    else:
        await ctx.channel.send(f'repeat channel is not set :open_mouth:')


##################################################################################################
##################################################################################################
## repeat_role
##  displays the current role to @ when a new member joins
##
@bot.command(pass_context=True)
async def repeat_role(ctx):
    global bot_settings

    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    
    guild = bot_settings[str(ctx.guild.id)]
    if guild is None:
        await ctx.channel.send('no repeat role is saved')
        return

    role = ctx.guild.get_role(guild['repeat_role'])
    if role is not None:
        await ctx.channel.send(f'repeat role is currently {role.name}')
    else:
        await ctx.channel.send(f'repeat role is not set :open_mouth:')


##################################################################################################
##################################################################################################
## join_notif
##  displays the current join notification message to print when a new member joins
##
@bot.command(pass_context=True)
async def join_notif(ctx):
    global bot_settings

    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    
    guild = bot_settings[str(ctx.guild.id)]

    notif = guild['join_notif']
    if notif is None:
        notif = default_join_notif

    await ctx.channel.send(f'join notification message is currently: {notif}')



##################################################################################################
##################################################################################################
## boop
##  fun method to boop yourself or another member
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

    
##################################################################################################
##################################################################################################
## on_ready
##  bot is ready to run.
##  initial startup things: 
##  * load the bot settings from the json file
##  * if the bot is running on a server with no settings, add a blank repeat option to the settings for it
##  * save the bot settings if there were changes
##
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    global bot_settings

    if os.path.exists(json_path):
        with open(json_path,'r+') as json_file:
            try:
                bot_settings = json.load(json_file)
            except JSONDecodeError:
                pass  
    initSize = len(bot_settings)

    for guild in bot.guilds:
        print(f'running on server: {guild.name} {guild.id}')
        if str(guild.id) not in bot_settings:
            bot_settings[str(guild.id)] = {'guild_name':guild.name, 'repeat_channel':None, 'repeat_role':None, 'join_notif':None}
            
    if len(bot_settings) > initSize:
        with open(json_path,'w') as json_file:
            json.dump(bot_settings, json_file)

            
##################################################################################################
##################################################################################################
## on_member_join
##  notify the appropriate channel and role there's a new memeber
##
@bot.event
async def on_member_join(ctx):
    global bot_settings
    bot_set = bot_settings[str(ctx.guild.id)]
    
    defaultChannel = ctx.guild.system_channel
    repeatChannel = ctx.guild.get_channel(bot_set['repeat_channel'])
    repeatRole = ctx.guild.get_role(bot_set['repeat_role'])

    if repeatChannel is not None:
        if repeatRole is not None:
            join_notif = None
            if 'join_notif' in bot_set:
                join_notif = bot_set['join_notif']

            if join_notif is None:
                join_notif = default_join_notif

            join_notif = join_notif.replace('[ROLE]', repeatRole.mention)
            join_notif = join_notif.replace('[NEWBIE]', ctx.mention)
            
            await repeatChannel.send(join_notif)
        else:
            await repeatChannel.send(f'Welcome to the mayhem, {ctx.mention}!')
    else:
        print(f'no repeat settings defined for guild: {ctx.guild.name}#{ctx.guild.id}')


token = os.environ['DISCORD_TOKEN'] #os.getenv('TOKEN') #
bot.run(token)


#######################################################
## TODO
## - store all unhandled newbs in DB
## - cmd: set nickname for newb
## - - make it remove the newb from teh db list
## - cmd: get list of unhandled newbs
## - cmd: remove newb from list
## - cmd: purge newb list

