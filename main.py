# ------------- Imports -----------------

import discord
from discord.ui import Button, View, Select
from discord.ext import commands
import os
import wolframalpha as wolf
from bs4 import BeautifulSoup
import requests
import re
import random
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import math
import asyncio
from collections import OrderedDict
from dotenv import load_dotenv
# ------------- Setups/Clients -----------------

# Wolfram
wolfClient = wolf.Client('XH8TAP-T2784E4RXJ')

# Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("-"),
                   intents=intents)

bot.remove_command('help')

# Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------- Utility Functions -----------------


async def send_msg(title, color, img, desc, message):
    embed = discord.Embed(title=title, description=desc, color=color)
    if img != '':
        embed.set_image(url=img)
    await message.send(embed=embed)


async def scrape(grade, channel):
    url = "https://www.geeksforgeeks.org/cbse-class-"+grade+"-maths-formulas/"
    res = requests.get(url)
    doc = BeautifulSoup(res.text, "html.parser")
    chap = doc.find_all(["h3"], text=re.compile("^Chapter.*"))
    options = []
    for i in range(0, len(chap)):
        cur = chap[i].string.split(":", 1)
        options.append(
            discord.SelectOption(
                label=cur[0], description=cur[1], value=chap[i].string)
        )

    embed = discord.Embed(
        title="Study Menu",
        description="Choose The Chapter You want to study from the dropdown",
        color=0x33CCCC
    )
    select = Select(options=options)

    async def handleChoice(interaction):
        c = doc.find(["h3"], text=select.values[0])
        c2 = c.next_sibling
        content = ''
        for a in list(c2.descendants):
            if str(a)[-4:] != '</a>':
                content += a
        c3 = c2.next_sibling
        while c3.name != "blockquote":
            c3 = c3.next_sibling

        lst = list(c3.children)[0]
        while lst.name != 'ol' and lst.name != 'ul':
            lst = lst.next_sibling

        concepts = ""

        for listItem in list(lst.children):
            curPt = ''
            for j in list(listItem.children):
                if len(str(j)) <= 2:
                    continue

                if str(j)[:1] == '<':
                    if str(j)[:3] == '<ol' or str(j)[:3] == 'ul':
                        continue
                    else:
                        try:
                            curPt += j.string
                        except:
                            continue
                else:
                    try:
                        curPt += j
                    except:
                        continue
            concepts += '> • '+curPt+'\n'
        embed = discord.Embed(
            title=select.values[0],
            description="**Introduction**:\n\n"+content +
            "\n\n**Concepts**\n\n"+concepts+"\n",
            color=0x33cccc
        )
        await interaction.response.send_message(embed=embed)

    select.callback = handleChoice

    view = View()
    view.add_item(select)

    embed.set_footer(text="Select Chapter to choose from Dropdown.")
    await channel.send(embed=embed, view=view)


async def sendMap(ctx, p1, p2):
    map = ""
    map += (':black_large_square:'*7)+':checkered_flag:\n'
    map += (':black_large_square:'*p1)+':blue_square:' + \
        (':black_large_square:'*(6-p1))+':checkered_flag:\n'
    map += (':black_large_square:'*7)+':checkered_flag:\n'
    map += (':black_large_square:'*p2)+':red_square:' + \
        (':black_large_square:'*(6-p2))+':checkered_flag:\n'
    map += (':black_large_square:'*7)+':checkered_flag:\n'

    await ctx.send(map)


async def sendProfData(ctx):

    userRef = db.collection('users').document(str(ctx.author.id))

    if not userRef.get().exists:
        await ctx.send("You have not set your profile yet. Use `-setup` to set your profile.")
        return

    userDoc = userRef.get()
    userDoc = userDoc.to_dict()

    embed = discord.Embed(
        title=f'{ctx.author} - PolyBot Profile',
        color=0x33cccc
    )
    embed.add_field(
        name="Game Data:-",
        value=f'''
        \n**Armor Level** : {userDoc['armor']}
        **Sword Level** : {userDoc['sword']}
        **XP** : {userDoc['exp']}
        **Coins** : {userDoc['money']}\n
        ''',
        inline=False
    )
    itemVal = ""
    dbItems = userDoc['items']
    if len(dbItems) == 0:
        itemVal = "*None*"
    else:
        for key, ct in dbItems.items():
            itemVal += "**"+str(key)+'** x '+str(ct)+'\n'
    embed.add_field(
        name="Items:-",
        value=itemVal,
        inline=False
    )
    await ctx.send(embed=embed)


# ------------- Events And Commands -----------------

@bot.event
async def on_ready():
    print('Logged on!')

# Flag Variables:
study_msg_id = -1
raceCheck = -1
racers = []


@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != study_msg_id:
        return
    if payload.member == bot.user:
        return
    emoji = str(payload.emoji)
    channel = bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
    if emoji == "1️⃣":
        await scrape('8', channel)
    elif emoji == "2️⃣":
        await scrape('9', channel)
    elif emoji == "3️⃣":
        await scrape('10', channel)


@bot.command()
async def setup(ctx):
    userRef = db.collection("users").document(str(ctx.author.id))
    if userRef.get().exists:
        await ctx.send("You Have Already Setup your PolyBot Account.")
        return

    waitMsg = await ctx.send("Initializing PolyBot Account Setup...")

    user = {
        "money": 0,
        "exp": 0,
        "items": {"nitro": 1, "potion": 1},
        "armor": 0,
        "sword": 0
    }

    db.collection("users").document(str(ctx.author.id)).set(user)
    await waitMsg.delete()
    await sendProfData(ctx)
    await ctx.send("Setup Complete! You can Now enjoy PolyBot freely. Use the `-help` command to get started.")


@bot.command()
async def delete(ctx):
    db.collection("users").document(str(ctx.author.id)).delete()
    await ctx.send("Deleted all data of your PolyBot Account.")


@bot.command()
async def pf(ctx):
    await sendProfData(ctx)


@bot.command()
async def shop(ctx):
    embed = discord.Embed(
        title="Shop",
        description='''
        **Upgrades**\n
        Armor :shield: : *100 Coins*
        Sword :crossed_swords: : *100 Coins*\n
        **Items**\n
        Potion :syringe: : *20 Coins*
        Nitro :fuel_pump: : *20 Coins*
        ''',
        color=0x33cccc
    )
    await ctx.send(embed=embed)


@bot.command()
async def buy(ctx, *, name):
    ref = db.collection('users').document(str(ctx.author.id))
    data = ref.get().to_dict()
    if name == 'Armor':
        if data["money"] >= 100:
            if data["armor"] >= 3:
                await ctx.send("Your Armor is at Max Level.")
            else:
                data["armor"] = data["armor"]+1
                data["money"] -= 100
                await ctx.send("Upgraded Armor Level to: "+str(data["armor"]))
        else:
            await ctx.send("Not Enough Money")
    elif name == "Sword":
        if data["money"] >= 100:
            if data["sword"] >= 3:
                await ctx.send("Your Sword is at Max Level.")
            else:
                data["sword"] = data["sword"]+1
                data["money"] -= 100
                await ctx.send("Upgraded Sword Level to: "+str(data["sword"]))
        else:
            await ctx.send("Not Enough Money.")
    elif name == "Potion":
        if data["money"] >= 20:
            data["items"]["potion"] = data["items"]["potion"]+1
            data["money"] -= 20
            await ctx.send("Potion Succesfully Bought.")
        else:
            await ctx.send("Not Enough Money.")
    elif name == "Nitro":
        if data["money"] >= 20:
            data["items"]["nitro"] = data["items"]["nitro"]+1
            data["money"] -= 20
            await ctx.send("Nitro Succesfully Bought.")
        else:
            await ctx.send("Not Enough Money.")
    else:
        await ctx.send("Item Does Not Exist.")
    ref.update(data)


@bot.command()
async def study(ctx):
    global study_msg_id
    # study_msg_id=msgID
    # await ctx.send(msgID)
    embed = discord.Embed(
        title='Class Menu',
        color=0x33CCCC,
        description='''
        :one:  **Class 8**
        
        :two:  **Class 9**
        
        :three:  **Class 10**
        ''',
    )
    sent = await ctx.send(embed=embed)
    study_msg_id = sent.id
    await sent.add_reaction("1️⃣")
    await sent.add_reaction("2️⃣")
    await sent.add_reaction("3️⃣")


@bot.command()
async def find(ctx, *, content):
    res = wolfClient.query(content)
    res = next(res.results).text
    await ctx.send(res)


@bot.command()
async def race(ctx, *, mention: discord.User):
    print(mention)
    racers = [ctx.message.author.id, mention.id]
    symbols = ['+', '-', '*']
    p1 = 0
    p2 = 0
    refP1 = db.collection('users').document(str(ctx.author.id))
    refP2 = db.collection('users').document(str(mention.id))
    dataP1 = refP1.get().to_dict()
    dataP2 = refP2.get().to_dict()
    await ctx.send(f':blue_square: - <@{ctx.message.author.id}>\n:red_square: - <@{mention.id}>\n')
    while p1 < 6 and p2 < 6:
        ques = str(random.randint(11, 99))+random.choice(symbols) + \
            str(random.randint(11, 99))
        await sendMap(ctx, p1, p2)
        await ctx.send(ques)
        ans = eval(ques)
        nitro1 = False
        nitro2 = False
        while True:
            userAns = await bot.wait_for('message')
            if userAns.content == "quit":
                if userAns.author.id == racers[0]:
                    await ctx.send(f"Player <@{racers[0]}> has quit the Race.")
                    p2 = 6
                    break
                elif userAns.author.id == racers[1]:
                    await ctx.send(f"Player <@{racers[1]}> has quit the Race.")
                    p1 = 6
                    break
            if userAns.content == "nitro":
                if userAns.author.id == racers[0]:
                    if dataP1["items"]["nitro"] > 0:
                        dataP1["items"]["nitro"] -= 1
                        nitro1 = True
                        await ctx.send(f"Player <@{racers[0]}> has used Nitro.")
                    else:
                        await ctx.send("You don't have any Nitro.")
                elif userAns.author.id == racers[1]:
                    if dataP2["items"]["nitro"] > 0:
                        dataP2["items"]["nitro"] -= 1
                        nitro2 = True
                        await ctx.send(f"Player <@{racers[1]}> has used Nitro.")
                    else:
                        await ctx.send("You don't have any Nitro.")
                continue
            print('ID: ', userAns.author.id)
            print('ans:', ans)
            print('Content: ', userAns.content)
            if userAns.author.id == racers[0]:
                if userAns.content == str(ans):
                    corDec = await ctx.send(f'<@{racers[0]}> - Correct Answer.')
                    p1 += 1
                    print(nitro1)
                    if nitro1:
                        print('Applied NITRO')
                        p1 += 1
                        nitro1 = False
                    break
                else:
                    if nitro1:
                        nitro1 = False
                    await ctx.send('Wrong')
            elif userAns.author.id == racers[1]:
                if userAns.content == str(ans):
                    corDec = await ctx.send(f'<@{racers[1]}> - Correct Answer.')
                    p2 += 1
                    if nitro2:
                        p2 += 1
                        nitro2 = False
                    break
                else:
                    if nitro2:
                        nitro2 = False
                    await ctx.send('Wrong')

    await sendMap(ctx, p1, p2)
    if p1 == 6:
        await ctx.send('<@'+str(racers[0])+'> gained 50 XP and 10 Coins.')
        refP1.update({
            "exp": dataP1["exp"]+50,
            "money": dataP1["money"]+10,
            "items": dataP1["items"]
        })
        refP2.update({"items": dataP2["items"]})
        await ctx.send(f":trophy: - <@{racers[0]}>\n")
    if p2 == 6:
        await ctx.send('<@'+str(racers[1])+'> gained 50 XP and 10 Coins.')
        refP2.update({
            "exp": dataP2["exp"]+50,
            "money": dataP2["money"]+10,
            "items": dataP2["items"]
        })
        refP1.update({"items": dataP1["items"]})
        await ctx.send(f":trophy: - <@{racers[1]}>\n")


@bot.command()
async def duel(ctx):
    refP1 = db.collection('users').document(str(ctx.author.id))
    dataP1 = refP1.get().to_dict()
    diff = ""
    if dataP1["exp"] <= 1000:
        diff = "easy"
    elif dataP1["exp"] <= 3000:
        diff = "medium"
    else:
        diff = "hard"
    question_api = requests.get(
        f"https://opentdb.com/api.php?amount=10&category=19&difficulty={diff}")
    data = eval(question_api.text)
    user_health = 20
    boss_health = 100
    run = True
    i = 0
    sharp = dataP1["sword"]
    prot = dataP1["armor"]
    while run:
        embed = discord.Embed(
            title='Boss Fight',
            color=0xee737e,
            description=f"""
   :dragon_face: - {boss_health}
   {":red_square:"*math.ceil(boss_health/10)}          



    {":green_square:"*math.ceil(user_health/4)}
    {user_health} - :ninja:  
"""
        )
        await ctx.send(embed=embed)
        if i > 9:
            i = 0
        question = data["results"][i]["question"]
        question_final = ''
        run2 = False
        for f in question:
            if f == "&":
                run2 = True
                continue
            if run2:
                if f == ";":
                    run2 = False
                continue
            question_final += f
        await ctx.send(question_final)
        correct_ans = data["results"][i]["correct_answer"]
        a, b, c, d = [10+(sharp*2), 15+(sharp*2), 4-prot, 7-prot]
        run1 = True
        while run1:
            user_ans = await bot.wait_for('message')
            if user_ans.author != ctx.author:
                continue
            if user_ans.content == "potion":
                if dataP1["items"]["potion"] > 0:
                    dataP1["items"]["potion"] -= 1
                    heal = random.randint(7, 10)
                    user_health += heal
                    if user_health > 20:
                        user_health = 20
                    await ctx.send(f"You chugged a potion and healed {heal} points of health")
            elif user_ans.content == "quit":
                await ctx.send("You fled")
                await ctx.send("While running away you lost 5 coins and also lost 10 exp")
                refP1.update({
                    "exp": dataP1["exp"]-10,
                    "money": dataP1["money"]-5,
                    "items": dataP1["items"]
                })
                run = False
                run1 = False
            elif user_ans.content == correct_ans:
                boss_health -= random.randint(a, b)
                await ctx.send("Correct Answer!! ")
                run1 = False
            elif user_ans.content != correct_ans:
                user_health -= random.randint(c, d)
                await ctx.send("Wrong Answer... ")
                run1 = False

        if boss_health <= 0:
            await ctx.send("Congratulatios!! You Won :trophy:")
            await ctx.send("You found 20 coins and got 100 XP")
            refP1.update({
                "exp": dataP1["exp"]+1000,
                "money": dataP1["money"]+20,
                "items": dataP1["items"]
            })

            run = False
        elif user_health <= 0:
            await ctx.send("Bad luck you lost... Try again or u can practice and come again :pensive:")
            await ctx.send("While running away for your life you dropped 10 coins")
            refP1.update({
                "exp": dataP1["exp"]+10,
                "money": dataP1["money"]-10,
                "items": dataP1["items"]
            })
            run = False
        i += 1


@bot.command()
async def stuff(ctx):
    refP1 = db.collection('users').document(str(ctx.author.id))
    dataP1 = refP1.get().to_dict()
    dataP1["items"]["potion"] += 10
    refP1.update({
        "items": dataP1["items"],
        "money": dataP1["money"]+1000
    })


def sort1(val):
    return val[1]


@bot.command()
async def lb(ctx):
    users = {}
    lb = []
    docs = db.collection('users').stream()
    a = 1
    for doc in docs:
        doc1 = doc.to_dict()
        li = [a, doc1["exp"]]
        users[doc.id] = li
        a += 1
    values = list(users.values())
    values.sort(key=sort1, reverse=True)
    for i in values:
        lb.append(list(users.keys())[list(users.values()).index(i)])
    lb_text = ""
    f = 1
    for i in lb:
        lb_text += f"{f}) "
        lb_text += str(await bot.fetch_user(i))
        lb_text += "\n"
        f += 1
    embed = discord.Embed(
        title="Leaderboard",
        color=0x33cccc,
        description=lb_text
    )
    await ctx.send(embed=embed)


@bot.command()
async def play(ctx):
    user = ctx.message.author
    voice_channel = user.voice.channel
    channel = None

    if voice_channel != None:

        channel = voice_channel.name
        await ctx.send('User is in channel: ' + channel)
        vc = await voice_channel.connect()
        player = vc.create_ffmpeg_player(
            'C:/Users/Administrator/OneDrive/Desktop/github/chatbot-shadytry2/Morning Coffee ☕️ [lofi hip hop_study beats].mp3', after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)

        player.stop()
        await vc.disconnect()
    else:
        await ctx.send('User is not in a channel.')


@bot.command()
async def help(ctx):
    general = discord.Embed(
        title="General Commands",
        color=0x33cccc,
    )
    general.add_field(
        name="`-setup`", value="Sets Up your discord account with PolyBot.", inline=False)
    general.add_field(
        name="`-pf`", value="Shows your Level,Exp,Money and Items of your PolyBot Game Data.", inline=False)
    general.add_field(
        name="`-delete`", value="Deletes all your discord account data with PolyBot.", inline=False)
    general.add_field(
        name="`-help`", value="Shows this message.", inline=False)
    await ctx.send(embed=general)

    study = discord.Embed(
        title="Learning Commands",
        color=0x33cccc
    )
    study.add_field(
        name="`-study`", value="Shows Important notes and formulas for different Mathematical Concepts.", inline=False)
    study.add_field(name="`-find <query>`",
                    value="Finds Answers for any mathematical query you ask.", inline=False)
    await ctx.send(embed=study)

    game = discord.Embed(
        title="Game Commands",
        color=0x33cccc
    )
    game.add_field(name="`-race <user>`",
                   value="Challenges another user to a Arithmetic Racing Game.", inline=False)
    game.add_field(
        name="`-duel`", value="Initiates a Math Trivia based Boss Fight.", inline=False)
    game.add_field(
        name="`-lb`", value="Shows Global Leaderboard of all PolyBot Game Players.", inline=False)
    await ctx.send(embed=game)

    shop = discord.Embed(
        title="Marketplace Commands",
        color=0x33cccc
    )
    shop.add_field(
        name="`-shop`", value="Shows all available Items and Upgrades in the PolyBot shop.", inline=False)
    shop.add_field(name="`-buy <item>`",
                   value="Buys the specified item from the shop.", inline=False)
    shop.add_field(name="`-buy <upgrade>`",
                   value="Buys an upgrade for your Sword/Armor increasing Offense/Defense in Duels.", inline=False)
    await ctx.send(embed=shop)


load_dotenv()
bot.run(os.environ["botKey"])
