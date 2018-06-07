#!/usr/bin/python3
import discord
import asyncio
import logging
import os
import json
import traceback

logging.basicConfig(level=logging.INFO)
client = discord.Client()
cache = {}

EMOJI_MAYBE = "❓"
EMOJI_X = "❌"
UNKNOW_PATERN = """Impossible de créer les slots.
Patern non reconnu : {tank}/{offtank}/{heal}/{cac}/{range}
exemple : /create raid-vétéran-nas-21h 1/1/2/4/4"""
UNKNOW_ROLE = "Erreur : Role non connu [tank/offtank/heal/cac/range]"
ROLE_IS_FULL = "Désolé, il n'y a plus de place pour ce role"
ALREADY_REGISTED = "Désolé, vous êtes déjà inscrit à cet évènement"
REGISTED = "{} s'est inscrit en tant que {} pour l'évenement"
UNREGISTED = "{} s'est désinscrit de l'évenement \"{}\""
FORCE_REGISTED = "{} a été inscrit de force de l'évenement {} par {}"
FORCE_UNREGISTED = "{} a été déscinscrit de force de l'évenement {} par {}"
NON_REGISTED = "La personne n'est pas inscrit à l'énènement"
NOT_FOUND = "Membre non trouvé, vérifiez le pseudo ou copiez l'ID"

DEFAULT_ROLE_LIST = ["tank", "offtank", "heal", "cac", "distant"]

@client.event
async def on_ready():
    print("Connected")

@client.event
async def on_message(message):
    try:
        if message.content.startswith('+'):
            await register(message)
        if message.content.startswith('/'):
            av = message.content.split(' ')
            if av[0] == "/create" : await create(message, av)
            if av[0] == "/unregister" : await unregister(message, av)
            if av[0] == "/forceregister" : await forceregister(message, av)
            if av[0] == "/forceunregister" : await forceunregister(message, av)
    except Exception:
        await message.channel.send("```diff\n-[Erreur]\n" + traceback.format_exc() + "```")


async def register(message):
    if str(message.channel.id) not in os.listdir("data"):
        return None
    role = message.content.split('+')[1].lower()
    data = load(message.channel.id)
    if message.author.id in concat_lists(data["registed"].values()):
        await message.channel.send(ALREADY_REGISTED)
        return None
    if role not in data["registed"].keys():
        await message.channel.send(UNKNOW_ROLE)
        return None
    if None not in data["registed"][role]:
        await message.channel.send(ROLE_IS_FULL)
        return None
    free_emplacement = data["registed"][role].index(None)
    data["registed"][role][free_emplacement] = message.author.id
    await message.channel.send(REGISTED.format(message.author.mention, role.capitalize()))
    save(message.channel.id, data)
    await display_slot(message.channel, data)
    return True


async def forceregister(message, av):
    try:
        id = int(av[1])
        id = str(id)
    except:
        try:
            member = message.guild.get_member_named(av[1])
            id = str(member.id)
        except:
            await message.channel.send(NOT_FOUND)
    data = load(message.channel.id)
    if do_unregister(data, id):
        await message.channel.send(FORCE_UNREGISTED.format(mention(id),
                                                           message.channel.name,
                                                           message.author.mention))
    else:
        await message.channel.send(NON_REGISTED)
    save(message.channel.id, data)
    await display_slot(message.channel, data)


async def unregister(message, av):
    data = load(message.channel.id)
    if do_unregister(data, id):
        await message.channel.send(UNREGISTED.format(message.author.mention,
                                                     message.channel.name))
    else:
        await message.channel.send(NON_REGISTED)
    save(message.channel.id, data)
    await display_slot(message.channel, data)


async def forceunregister(message, av):
    try:
        id = int(av[1])
        id = str(id)
    except:
        try:
            member = message.guild.get_member_named(av[1])
            id = str(member.id)
        except:
            await message.channel.send(NOT_FOUND)
    data = load(message.channel.id)
    if do_unregister(data, id):
        await message.channel.send(FORCE_UNREGISTED.format(mention(id),
                                                           message.channel.name,
                                                           message.author.mention))
    else:
        await message.channel.send(NON_REGISTED)
    save(message.channel.id, data)
    await display_slot(message.channel, data)


def do_unregister(data, id):
    for plist in data["registed"].values():
        for i in range(len(plist)):
            if str(plist[i]) == str(id) :
                plist[i] = None
                return True
    return False

async def create(message, av):
    canal_name = av[1]
    slot = av[2].split('/')
    canal = await message.guild.create_text_channel(canal_name, category=message.channel.category)
    data = await create_data(canal, slot)
    await display_slot(canal, data)

    
async def create_data(canal, slot):
    data = {"registed":{}, "msg":None}
    for i in range(len(slot)):
        if ':' in slot[i]:
            data["registed"][slot[i].split(':')[0]] = [None] * int(slot[i].split(':')[1])
        else:
            data["registed"][DEFAULT_ROLE_LIST[i]] = [None] * int(slot[i])
    cache[canal.id] = await canal.send("Loading slot ...")
    await cache[canal.id].add_reaction(EMOJI_MAYBE)
    await cache[canal.id].add_reaction(EMOJI_X)
    await cache[canal.id].pin()
    data["msg"] = cache[canal.id].id
    save(canal.id, data)
    return (data)


async def display_slot(channel, data):
    txt = "Place restante : " + str(concat_lists(data["registed"].values()).count(None))
    for role, plist in data["registed"].items():
        for player in plist:
            txt += "\n{} : {}".format(role.capitalize(), mention(player) if player else "")
    try:
        message = cache[str(channel.id)]
    except:
        message = await channel.get_message(int(data["msg"]))
    await message.edit(content=txt)
    return (txt)


def load(id):
    with open("data/{}".format(id), 'r') as fd:
        data = json.loads(fd.read())
    return (data)

def save(nb, data):
    with open("data/{}".format(nb), 'w') as fd:
        fd.write(json.dumps(data))
    return None

def concat_lists(lists):
    result = []
    for i in lists:
        result += i
    return (result)

def mention(x):
    return ("<@{}>".format(x))

with open("token.txt", 'r') as fd:
    token = fd.read().replace('\n', '')
client.run(token, bot=True)
