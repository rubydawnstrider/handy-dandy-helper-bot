# bot.py
import discord
import os
from discord.ext import commands
import pymongo
from pymongo import MongoClient

#from dotenv import load_dotenv
#load_dotenv()

cluster = MongoClient(os.environ['MONGO_CONN'])
db = cluster['handy-dandy-helper-mofo']
collection = db['config-data']

client = discord.Client()

bot = commands.Bot(command_prefix='!')

@bot.command
async def set_repeat_channel(ctx, arg):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    if arg is None or arg == '':
        await ctx.channel.send('huh? you need to provide a channel name')
        return

    channel_id = None
    for channel in ctx.guild.channels:
        if channel.name == arg:
            channel_id = str(channel.id)
            break

    if channel_id is None:
        await ctx.channel.send('you need to provide a valid channel name')
        return
        
    #server should have been added in setup so we'll assume its available to update
    collection.update_one({'_id': str(ctx.guild.id)}, {'$set':{'repeat_channel': channel_id}})
    await ctx.channel.send(f'repeat channel saved as {arg}')
    

@bot.command
async def repeat_channel(ctx):
    if ctx.guild is None:
        await ctx.channel.send('this is only designed to run on a server')
        return
    
    query = {'_id': str(ctx.guild.id)}
    guild = collection.find_one(query)
    if quild is None:
        await ctx.channel.send('no repeat channel is saved')
        return

    channel = guild['repeat_channel']
    await ctx.channel.send(f'repeat channel is currently {channel}')


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    for guild in client.guilds:
        print(f'running on server: {guild.name} {guild.id}')
        # if we didnt add a setting for the server yet, add it
        if (collection.count_documents({'_id': str(guild.id) }) == 0):
            print(f'adding server: {guild.name} {guild.id} to the DB . . .')
            server = {'_id': str(guild.id), 'guild_name': guild.name}
            collection.insert_one(server)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    message.author = client.user
    print(f'msg:~{message.content}~')
    new_msg = 'repeat: ' + message.content
    await message.channel.send(new_msg)

client.run(os.environ['DISCORD_TOKEN'])
