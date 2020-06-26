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

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    for guild in client.guilds:
        print(f'server: {guild.name} {guild.id}')
        post = {"_id": guild.id, "guild_name": guild.name}
        collection.insert_one(post)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    message.author = client.user
    print(f'msg:~{message.content}~')
    new_msg = 'repeat: ' + message.content
    await message.channel.send(new_msg)

client.run(os.environ['DISCORD_TOKEN'])
