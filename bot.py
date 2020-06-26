# bot.py
import os

import discord

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    for guild in client.guilds:
        print(f'server: {guild.name} {guild.id}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    message.author = client.user
    print(f'msg:~{message.content}~')
    new_msg = 'repeat: ' + message.content
    await message.channel.send(new_msg)

client.run(TOKEN)
