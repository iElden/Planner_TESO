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
EMOJI_RESERVIST = "🇷"
UNKNOW_PATERN = """Impossible de créer les slots.
Patern non reconnu : {tank}/{offtank}/{heal}/{cac}/{range}
exemple : /create raid-vétéran-nas-21h 1/1/2/4/4"""
UNKNOW_ROLE = "Erreur : Rôle non connu [{}]"
ROLE_IS_FULL = "Désolé, il n'y a plus de place pour ce role"
ALREADY_REGISTED = "Désolé, vous êtes déjà inscrit à cet évènement"
REGISTED = "{} s'est inscrit en tant que {} pour l'évenement"
UNREGISTED = "{} s'est désinscrit de l'évenement \"{}\""
FORCE_REGISTED = "{} a été inscrit de force de l'évenement {} par {} au role de {}"
FORCE_UNREGISTED = "{} a été déscinscrit de force de l'évenement {} par {}"
NON_REGISTED = "La personne n'est pas inscrit à l'énènement"
NOT_FOUND = "Membre non trouvé, vérifiez le pseudo ou copiez l'ID"
INVALID_SYNTAX_SLOT = "Syntaxe invalide : /slot {role} {nombre} (/slot tank 2)"
FORBIDDEN = "Vous n'êtes pas autorisé à utiliser cette commande"

DEFAULT_ROLE_LIST = ["tank", "offtank", "heal", "cac", "distant"]

@client.event
async def on_ready():
    roles = client.get_guild(298108708813013002).roles
    for role in roles:
        print(role.name, role.permissions.manage_channels)

@client.event
async def on_raw_reaction_add(payload):
    try:
        channel = payload.channel_id
        await display_slot(client.get_channel(channel), load(channel))
    except:
        pass

@client.event
async def on_raw_reaction_remove(payload):
    channel = payload.channel_id
    await display_slot(client.get_channel(channel), load(channel))

@client.event
async def on_message(message):
    try:
        if message.content.startswith('+'):
            await register(message)
        if message.content.startswith('/'):
            av = message.content.split(' ')
            while '' in av : av.remove('')
            if av[0] == "/create" : await create(message, av, create=True)
            if av[0] == "/init" : await create(message, av, create=False)
            if av[0] == "/unregister" : await unregister(message, av)
            if av[0] == "/forceregister" : await forceregister(message, av)
            if av[0] == "/forceunregister" : await forceunregister(message, av)
            if av[0] == "/slot" : await change_slot(message, av)
            if av[0] == "/move" : await move_all(message, av)
            if av[0] == "/sendmessage" : await sendmessage(message, av)
            if av[0] == "/changedescription" : await change_description(message, av)
    except Exception:
        await message.channel.send("```diff\n-[Erreur]\n" + traceback.format_exc() + "```")


async def is_authorised(message):
    if message.author.id == 384274248799223818: return True
    perm = message.author.guild_permissions
    if perm.administrator or perm.manage_channels or perm.manage_guild:
        return True
    await message.channel.send(FORBIDDEN)
    return False

async def register(message):
    if str(message.channel.id) not in os.listdir("data"):
        return None
    role = message.content.split('+')[1].lower()
    data = load(message.channel.id)
    if message.author.id in concat_lists(data["registed"].values()):
        await message.channel.send(ALREADY_REGISTED)
        return None
    if role not in data["registed"].keys():
        await message.channel.send(UNKNOW_ROLE.format("/".join([i for i in data["registed"].keys() if data["registed"][i]])))
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
    if not await is_authorised(message):
        return False
    try:
        id = int(av[1])
        id = str(id)
    except:
        try:
            member = message.guild.get_member_named(av[1])
            id = str(member.id)
        except:
            await message.channel.send(NOT_FOUND)
    try:
        role = av[2].lower()
    except:
        await message.channel.send("Il faut préciser le rôle pour le /forceregister")
        return None
    data = load(message.channel.id)
    if id in concat_lists(data["registed"].values()):
        await message.channel.send("Déjà inscrit.")
        return None
    if role in data["registed"]:
        try:
            free_emplacement = data["registed"][role].index(None)
            data["registed"][role][free_emplacement] = id
        except:
            data["registed"][role].append(id)
    else:
        data["registed"][role] = [id]
    await message.channel.send(FORCE_REGISTED.format(mention(id),
                                                     message.channel.name,
                                                     message.author.mention,
                                                     role))
    save(message.channel.id, data)
    await display_slot(message.channel, data)


async def unregister(message, av):
    data = load(message.channel.id)
    if do_unregister(data, message.author.id):
        await message.channel.send(UNREGISTED.format(message.author.mention,
                                                     message.channel.name))
    else:
        await message.channel.send(NON_REGISTED)
        return None
    save(message.channel.id, data)
    await display_slot(message.channel, data)


async def forceunregister(message, av):
    if not await is_authorised(message):
        return False
    try:
        id = int(av[1])
        id = str(id)
    except:
        try:
            member = message.guild.get_member_named(av[1])
            id = str(member.id)
        except:
            await message.channel.send(NOT_FOUND)
            return None
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

async def create(message, av, create=True):
    if not await is_authorised(message):
        return False
    canal_name = av[1]
    slot = av[2].split('/')
    if create:
        canal = await message.guild.create_text_channel(canal_name, category=message.channel.category)
    else:
        canal = message.channel
    data = await create_data(canal, slot, desc=' '.join(av[3:]) if len(av) > 3 else "")
    await display_slot(canal, data)

    
async def create_data(canal, slot, desc=""):
    data = {"registed":{}, "msg":None, "description":desc}
    for i in range(len(slot)):
        if ':' in slot[i]:
            data["registed"][slot[i].split(':')[0]] = [None] * int(slot[i].split(':')[1])
        else:
            data["registed"][DEFAULT_ROLE_LIST[i]] = [None] * int(slot[i])
    cache[canal.id] = await canal.send("Loading slot ...")
    await cache[canal.id].add_reaction(EMOJI_RESERVIST)
    await cache[canal.id].add_reaction(EMOJI_MAYBE)
    await cache[canal.id].add_reaction(EMOJI_X)
    await cache[canal.id].pin()
    data["msg"] = cache[canal.id].id
    save(canal.id, data)
    return (data)


async def display_slot(channel, data):
    desc = data.get("description") or ""
    txt = desc + "\nPlace restante : " + str(concat_lists(data["registed"].values()).count(None))
    for role, plist in data["registed"].items():
        for player in plist:
            txt += "\n{} : {}".format(role.capitalize(), mention(player) if player else "")
    try:
        message = cache[str(channel.id)]
    except:
        message = await channel.get_message(int(data["msg"]))

    txt += '\n'
    for reaction in message.reactions:
        members = await reaction.users().flatten()
        if reaction.emoji == EMOJI_RESERVIST:
            txt += "\nreserviste (R) : "
            txt += ", ".join([member.mention for member in members if member != client.user])
        elif reaction.emoji == EMOJI_MAYBE:
            txt += "\npeut-être (?) : "
            txt += ", ".join([member.mention for member in members if member != client.user])
        elif reaction.emoji == EMOJI_X:
            txt += "\nabsent (X) : "
            txt += ", ".join([member.mention for member in members if member != client.user])
    await message.edit(content=txt)
    return (txt)

async def change_slot(message, av):
    if not await is_authorised(message):
        return False
    if len(av) != 3:
        await message.channel.send(INVALID_SYNTAX_SLOT)
    role = av[1].lower()
    nb = int(av[2])
    data = load(message.channel.id)
    if role not in data["registed"]:
        data["registed"][role] = [None] * nb
    elif len(data["registed"][role]) < nb:
        data["registed"][role] += [None] * (nb - len(data["registed"][role]))
    elif len(data["registed"][role]) > nb:
        while None in data["registed"][role] and len(data["registed"][role]) > nb:
            data["registed"][role].remove(None)
        while len(data["registed"][role]) > nb:
            await forceunregister(message, [None, data["registed"][role][-1]])
            data["registed"][role] = data["registed"][role][:-1]
    save(message.channel.id, data)
    await message.channel.send("Nombre de slot modifié")
    await display_slot(message.channel, data)

async def change_description(message, av):
    if not await is_authorised(message):
        return False
    data = load(message.channel.id)
    data['description'] = ' '.join(av[1:])
    save(message.channel.id, data)
    await display_slot(message.channel, data)

async def sendmessage(message, av):
    if not await is_authorised(message):
        return False
    pass


async def move_all(message, av):
    if not await is_authorised(message):
        return False
    try:
        id = int(av[1])
        id = str(id)
    except:
        try:
            canal = discord.utils.get(message.guild.channels, name=" ".join(av[1:]))
            id = str(canal.id)
        except:
            await message.channel.send("Canal non trouvé")
            return None
    try:
        canal = message.guild.get_channel(int(id))
        if not canal : raise ValueError
    except:
        await message.channel.send("Canal non trouvé.")
        return None
    data = load(message.channel.id)
    plist = [i for i in concat_lists(data["registed"].values()) if i]
    players_in_channel = canal.members
    for i in plist:
        member = message.guild.get_member(i)
        try:
            if member not in players_in_channel:
                await member.move_to(canal)
        except:
            await message.channel.send("Impossible de move " + (member.name if member else str(i)))

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
