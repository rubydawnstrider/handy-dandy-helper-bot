# bot.py
import discord
import os
from discord.ext import commands
import pymongo
from pymongo import MongoClient

#from dotenv import load_dotenv
#load_dotenv()

url_conn = os.environ['MONGO_CONN'] #os.getenv('CONN') #
cluster = MongoClient(url_conn)
db = cluster['handy-dandy-helper-mofo']
collection = db['config-data']

bot = commands.Bot(command_prefix='!')

@bot.command(pass_context=True)
async def settings(ctx):
    query = {'_id':str(ctx.guild.id)}
    data = collection.find_one(query)
    if data is not None:
        chQuery = {'_id':str(ctx.guild.id),'repeat_channel':{'$exists':True,'$ne':None}}
        ch = collection.find_one(chQuery)
        channel = None
        if ch is not None:
            channel = ctx.guild.get_channel(ch)
        roleQuery = {'_id':str(ctx.guild.id),'repeat_role':{'$exists':True,'$ne':None}}
        r = collection.find_one(roleQuery)
        role = None
        if r is not None:
            role = ctx.guild.get_role(role)

        printOut = 'HandyDandyHelperMofo settings\n  repeat channel: '
        if channel is not None:
            printOut = printOut + channel.mention
        printOut = printOut + '\n  repeat role: '
        if role is not None:
            printOut = printOut + role.mention

        print(printOut)
        await ctx.channel.send(printOut)

            
@bot.command(pass_context=True)
async def set_repeat_ch(ctx, arg:discord.TextChannel):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    if arg is None:
        await ctx.channel.send('huh? you need to provide a channel')
        return

    #server should have been added in setup so we'll assume its available to update
    collection.update_one({'_id': str(ctx.guild.id)}, {'$set':{'repeat_channel': arg.id}})
    await ctx.channel.send(f'repeat channel saved as {arg.mention}')


@bot.command(pass_context=True)
async def set_repeat_role(ctx, arg:discord.Role):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    if arg is None:
        await ctx.channel.send('huh? you need to provide a role')
        return

    #server should have been added in setup so we'll assume its available to update
    collection.update_one({'_id': str(ctx.guild.id)}, {'$set':{'repeat_role': arg.id}})
    await ctx.channel.send(f'repeat role saved as {arg.mention}')
    

@bot.command(pass_context=True)
async def repeat_ch(ctx):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    
    query = {'_id': str(ctx.guild.id), 'repeat_channel':{'$exists':True,'$ne':None} }
    guild = collection.find_one(query)
    if guild is None:
        await ctx.channel.send('no repeat channel is saved')
        return

    channel = ctx.guild.get_channel(guild['repeat_channel'])
    if channel is not None:
        await ctx.channel.send(f'repeat channel is currently {channel.mention}')
    else:
        await ctx.channel.send(f'repeat channel is set but could not be found on the server :o')


@bot.command(pass_context=True)
async def repeat_role(ctx):
    print(f'get repeat role for server:{ctx.guild.id}')
    
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    
    query = {'_id': str(ctx.guild.id), 'repeat_role':{'$exists':True,'$ne':None} }
    guild = collection.find_one(query)
    if guild is None:
        await ctx.channel.send('no repeat role is saved')
        return

    role = ctx.guild.get_role(guild['repeat_role'])
    if role is not None:
        await ctx.channel.send(f'repeat role is currently {role.name}')
    else:
        await ctx.channel.send(f'repeat role is set but could not be found on the server :o')


@bot.command(pass_context=True)
async def boop(ctx):
    author = ctx.message.author.mention
    await ctx.channel.send(f'**BOOP, {author}!**')

    
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    for guild in bot.guilds:
        print(f'running on server: {guild.name} {guild.id}')
        # if we didnt add a setting for the server yet, add it
        query = {'_id': str(guild.id)}
        g0 = collection.find_one(query)
        if g0 is None:
            print(f'adding server: {guild.name} {guild.id} to the DB . . .')
            server = {'_id': str(guild.id), 'guild_name': guild.name}
            collection.insert_one(server)


@bot.event
async def on_member_join(ctx):
    query = {'_id': str(ctx.guild.id)}
    guild = collection.find_one(query)
    defaultChannel = ctx.guild.system_channel
    repeatChannel = ctx.guild.get_channel(guild['repeat_channel'])
    repeatRole = ctx.guild.get_role(guild['repeat_role'])

#    print(f'join: {ctx}')
#    await defaultChannel.send(f'repeat channel: {repeatChannel.mention}')
#    await defaultChannel.send(f'repeat role: {repeatRole.mention}')

    if repeatChannel is not None:
        if repeatRole is not None:
            await repeatChannel.send(f'Yo, {repeatRole.mention}. Newb alert: {ctx.mention}! Better make sure they got the right nickname and role')
        else:
            await repeatChannel.send(f'Welcome to the mayhem, {ctx.mention}!')
    

@bot.event
async def on_message(ctx):
    if ctx.author == bot.user:
        return

    #dont process here if this is a command for the bot
    if ctx.content.startswith(bot.command_prefix):
        await bot.process_commands(ctx)
        return

    if ctx.type == discord.MessageType.new_member:
        return
    
    print(f'msg:~{ctx.content} | {ctx.type}~')
##    new_msg = 'repeat: ' + message.content
##    await message.channel.send(new_msg)

token = os.environ['DISCORD_TOKEN'] #os.getenv('TOKEN') #
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

