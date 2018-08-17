import discord
import asyncio
import logging
import os
import json
import traceback

logging.basicConfig(level=logging.INFO)
client = discord.Client()
EMOJI_RESERVIST = "🇷"

@client.event
async def on_message(message):
    if message.content == "/update":
        pinned = await message.channel.pins()
        msg = pinned[0]
        await msg.add_reaction(EMOJI_RESERVIST)

with open("token.txt", 'r') as fd:
    token = fd.read().replace('\n', '')
client.run(token, bot=True)
