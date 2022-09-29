# ------------- Imports -----------------

import discord
from discord.ui import Button, View, Select
from discord.ext import commands
import os
from dotenv import load_dotenv
import wolframalpha as wolf
from bs4 import BeautifulSoup
import requests
import re
import random
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time


# ------------- Setups/Clients -----------------

# Wolfram
wolfClient = wolf.Client('XH8TAP-T2784E4RXJ')

# Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("-"),
                   intents=intents)

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
        \n**Level** : {userDoc['level']}
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
        "items": {"nitro": 1},
        "level": 1
    }

    db.collection("users").document(str(ctx.author.id)).set(user)
    await waitMsg.delete()
    await sendProfData(ctx)
    await ctx.send("Setup Complete! You can Now enjoy PolyBot freely. Use the `-help` command to get started.")


@bot.command()
async def delete(ctx):
    del db[str(ctx.author.id)]


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
        if ref["money"] >= 100:
            if ref["armor"] >= 3:
                await ctx.send("Your Armor is at Max Level.")
            else:
                data["armor"] = data["armor"]+1
                data["money"] -= 100
                await ctx.send("Upgraded Armor Level to: "+str(ref["armor"]+1)+'.')
        else:
            await ctx.send("Not Enough Money")
    elif name == "Sword":
        if ref["money"] >= 100:
            if ref["sword"] >= 3:
                await ctx.send("Your Sword is at Max Level.")
            else:
                data["sword"] = data["sword"]+1
                data["money"] -= 100
                await ctx.send("Upgraded Sword Level to: "+str(ref["sword"]+1)+'.')
        else:
            await ctx.send("Not Enough Money.")
    elif name == "Potion":
        if ref["money"] >= 20:
            data["items"]["potion"] = data["items"]["potion"]+1
            data["money"] -= 20
            await ctx.send("Potion Succesfully Bought.")
        else:
            await ctx.send("Not Enough Money.")
    elif name == "Nitro":
        if ref["money"] >= 20:
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
            if userAns.content == "nitro":
                print("SAID NITRO")
                if userAns.author.id == racers[0]:
                    if dataP1["items"]["nitro"] > 0:
                        dataP1["items"]["nitro"] -= 1
                        nitro1 = True
                elif userAns.author.id == racers[1]:
                    if dataP2["items"]["nitro"] > 0:
                        dataP2["items"]["nitro"] -= 1
                        nitro2 = True
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
        refP2.update({
            "exp": dataP2["exp"]+50,
            "money": dataP2["money"]+10,
            "items": dataP2["items"]
        })
        refP1.update({"items": dataP1["items"]})
        await ctx.send(f":trophy: - <@{racers[1]}>\n")


@bot.command()
async def duel(ctx):
    user_health = 20
    boss_health = 100
    run = True
    while run:
        await ctx.send(f"""
|--------------------|
|   boss - {boss_health}          |
|                                |
|                                |
|                                |
|               {user_health} - You  |
|--------------------|""")
        question = "What is 1+1"
        options = ["0", "1", "2", "3"]
        a, b, c, d = [10, 15, 4, 6]
        correct_ans = "2"
        user_ans = ""
        await ctx.send(question)
        view = View()
        button = Button(
            label=f"1)  {options[0]}",
            custom_id="1",
            style=discord.ButtonStyle.green
        )

        async def response(interaction):
            await interaction.response.send_message(button.label)
        button.callback = response

        button1 = Button(
            label=f"2)  {options[1]}",
            custom_id="2",
            style=discord.ButtonStyle.green
        )

        async def response1(interaction):
            await interaction.response.send_message(button1.label)
        button1.callback = response1

        button2 = Button(
            label=f"3)  {options[2]}",
            custom_id="3",
            style=discord.ButtonStyle.green
        )

        async def response2(interaction):
            await interaction.response.send_message(button2.label)
        button2.callback = response2

        button3 = Button(
            label=f"4)  {options[3]}",
            custom_id="4",
            style=discord.ButtonStyle.green
        )

        async def response3(interaction):
            await interaction.response.send_message(button3.label)
        button3.callback = response3

        view.add_item(button3)
        view.add_item(button2)
        view.add_item(button1)
        view.add_item(button)
        await ctx.send(" ", view=view)
        time.sleep(30)
        if user_ans == correct_ans:
            boss_health -= random.randint(a, b)
        elif user_ans != correct_ans:
            user_health -= random.randint(c, d)

        if boss_health <= 0:
            await ctx.send("Congratulatios!! You Won")
            run = False
        elif user_health <= 0:
            await ctx.send("Bad luck you lost... Try again if u want or u can practice and come again")
            run = False


@bot.command()
async def lb(ctx):
    q = db.collection("users").order_by(
        "exp", direction=firestore.Query.DESCENDING).limit(5)
    dt = q.get()
    res = []
    ctr = 1
    for i in dt:
        ctr += 1
        res.append(str(i)+'\t**'+str(i.name)+'**\t' +
                   str(i.exp)+' \$'+str(i.money))
    embed = discord.Embed(
        title="LeaderBoard",
        description=res.join('\n'),
        color=0x33cccc
    )
    await ctx.send(embed=embed)

load_dotenv()
bot.run(os.environ['botKey'])
