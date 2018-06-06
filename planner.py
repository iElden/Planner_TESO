#!/usr/bin/python3
import discord
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)
client = discord.Client()

UNKNOW_PATERN = """Impossible de créer les slots.
Patern non reconnu : {tank}/{offtank}/{heal}/{cac}/{range}
exemple : /create raid-vétéran-nas-21h 1/1/2/4/4"""
UNKNOW_ROLE = "Erreur : Role non connu [tank/offtank/heal/cac/range]"
ROLE_IS_FULL = "Désolé, il n'y a plus de place pour ce role"
ALREADY_REGISTED = "Désolé, vous êtes déjà inscrit à cet évènement"
REGISTED = "{} s'est inscrit en tant que {} pour l'évenement"

DEFAULT_ROLE_LIST = ["tank", "offtank", "heal", "cac", "range"]

@client.event
async def on_ready():
    print("Connected")

@client.event
async def on_message(message):
    if m.content.startswith('+'):
        return (register(message))
    if m.content.startswith('/'):
        return None


async def register(message):
    if m.channel.id not in os.listdir("data"):
        return None
    role = message.content.split('+')[1].lower()
    data = load(channel.id)
    if message.author.id in concat_lists(data["registed"].values()):
        await message.channel.send(ALREADY_REGISTED)
    if role not in data["registed"].keys():
        await message.channel.send(UNKNOW_ROLE)
        return None
    if None not in data["registed"][role]:
        await message.channel.send(ROLE_IS_FULL)
        return None
    replace(None, message.author.id)
    await message.channel.send(REGISTED.format(message.author.mention, role.capitalize()))
    save(channel.id, data)


async def create(message, av):
    canal_name = av[1]
    slot = av[2].split('/')
    if len(slot) != 5:
        await message.channel.send(UNKNOW_PATERN)


def concat_lists(lists):
    result = []
    for i in lists:
        result += i
    return (result)
