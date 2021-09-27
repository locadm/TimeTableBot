# bot.py
import asyncio
import glob
import os
import pickle
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import datetime


class Database:
    def __init__(self):
        self.accounts = []


class Account:
    def __init__(self, discord_id):
        self.discord_id = discord_id
        self.events = []


class Event:
    def __init__(self, day, time, url):
        self.day = day
        self.time = time
        self.url = url


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix='!')
intents = discord.Intents.all()
intents.members = True
database = Database()

if os.path.exists("pickle.txt"):
    print("Súbor databázy bol nájdený...")
else:
    print("SUBOR DATABAZY NEBOL NAJDENY...")
    print("VYTAVARAM SUBOR...")
    f = open("pickle.txt", "x")
    print("VYTAVARAM NOVU...")
    database = Database()

if os.path.getsize("pickle.txt") == 0:
    print("PICKLE DATABAZY BOL PRAZDNY VYTVARAM NOVU DATABAZU")
    database = Database()
    f = open("pickle.txt", "wb")
    pickle.dump(database, f)
    f.close()

else:
    print("Pickle databázy nie je prazdny")
    infile = open("pickle.txt", 'rb')
    database = pickle.load(infile)
    infile.close()


@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(guild.name)

    print(
        f'\n{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    bot.loop.create_task(check_time())


@bot.command(name="nuke", brief="DM_ONLY: Vymaže všetky nastavené upozornenia")
async def nuke(ctx):
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.author.send("Vážne chceš vymazať všetky upozornenia?")

        try:
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=10)
            msg = msg.content.lower()
            print(msg)

            if msg == "ano" or msg == "áno" or msg == "yes" or msg == "y" or msg == "1":

                print(str(ctx.author.id) + "AA\n")
                for people in database.accounts:
                    print(str(people.discord_id) + "\n")

                for person in database.accounts:
                    if person.discord_id == ctx.author.id:
                        database.accounts.remove(person)
                        pickle_database()
                        await ctx.author.send(file=discord.File('media/nuke.gif'))
                        await ctx.author.send("Všetky záznamy boli úspešne vymazané")
            else:
                await ctx.author.send("**Ruším požiadavku na vymazanie**")

        except asyncio.exceptions.TimeoutError:
            await ctx.author.send("**Vypršal čas na odpoveď, ruším príkaz...**")


@bot.command(name="pickmeup", brief="Awww", aliases=["aww"])
async def pickmeup(ctx):
    print("COMMAND: PICK ME UP")
    images = glob.glob("media/eyebleach/*.jpg")
    random_image = random.choice(images)
    await ctx.channel.send(file=discord.File(random_image))


@bot.command(name="setup", brief="Vezme používateľa do DMa a predstaví sa")
async def setup(ctx):
    await ctx.author.send(f"Som TimeTableBot alebo TTBot read. (TittyBot) v tomto DM si nastavíš upozornenia na hodiny"
                          f" ktoré ti budem posielať 5 minút pred začiatkom"
                          f"\n\n"
                          f"**Ak potrebuješ pomôcť použi príkaz `!help`**")


@bot.command(name="display", brief="Vypísanie nastavených upozornení", aliases=["d"])
async def display(ctx):
    to_send = "**Uložené upozornenia:** ```"

    for person in database.accounts:
        if person.discord_id == ctx.author.id:
            for event in person.events:
                to_send = to_send + uncode_day(event.day) + " " + uncode_hour(event.time) + " " + event.url + "\n"
            to_send = to_send + "```"
            await ctx.author.send(to_send)
            return

    await ctx.author.send("Nemáš vytvorené žiadne upozornenia!")


@bot.command(name="add", brief="Pridanie upozornenia vo formáte !add d hhmm link", aliases=["a"])
async def add(ctx, day, hour, link):
    await ctx.author.send(
        "Vytvoril som upozornenie na " + uncode_day(day) + " " + uncode_hour(hour) + " s linkom " + link)
    add_event_to_database(ctx.author.id, day, hour, link)
    pickle_database()


@bot.command(name="delete", brief="Odstránenie vybraného upozornenia", aliases=["del"])
async def delete(ctx):
    if isinstance(ctx.channel, discord.channel.DMChannel):

        message = "**Zadaj číslo upozornenia ktoré chceš vymazať:**```"
        counter = 1

        for person in database.accounts:
            if int(person.discord_id) == ctx.author.id:
                for event in person.events:
                    message = message + "(" + str(counter) + "): \t" + uncode_day(event.day) + " " + \
                              uncode_hour(event.time) + " " + event.url + "\n"
                    counter += 1
                break
        message += "```"
        await ctx.author.send(message)

        try:
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
            if not msg.content.isnumeric():
                await ctx.author.send("**Zadaný vstup nie je platný, ruším príkaz...**")
                return
            msg = int(msg.content) - 1
            if len(person.events) > msg > 0:
                person.events.pop(msg)
                pickle_database()
                await ctx.author.send("Upozornenie bolo úspešne vymazané")
        except asyncio.exceptions.TimeoutError:
            await ctx.author.send("**Vypršal čas na odpoveď, ruším príkaz...**")


async def check_time():
    while True:
        await send_alerts()
        await asyncio.sleep(60)


async def send_alerts():
    now = datetime.datetime.now()
    then = now + datetime.timedelta(minutes=5)
    current_time = now.strftime("%H%M")
    announce_time = then.strftime("%H%M")
    day = now.weekday()+1
    print(uncode_hour(current_time)+" : Kontrolujem upozornenia na: " + uncode_hour(announce_time))

    for person in database.accounts:
        for event in person.events:
            if event.time == announce_time and day == int(event.day):
                user = await bot.fetch_user(person.discord_id)
                print("Posielam upozornenie uživatelovi " + user.display_name + " na čas: " + uncode_day(event.day) +
                      " " + uncode_hour(event.time))
                await user.send("Upozornenie na udalosť:\n" + uncode_day(event.day) + " " + uncode_hour(event.time) +
                                "\n" + event.url)


def pickle_database():
    file = open("pickle.txt", "wb")
    pickle.dump(database, file)
    file.close()


def uncode_hour(hour):
    return hour[:2] + ":" + hour[2:]


def uncode_day(day):
    day = day.lower()
    if day == '1':
        return "PONDELOK"
    if day == '2':
        return "UTOROK"
    if day == '3':
        return "STREDA"
    if day == '4':
        return "ŠTVRTOK"
    if day == '5':
        return "PIATOK"

    return "ERROR"


def add_event_to_database(discord_id, day, time, url):

    new_event = Event(day, time, url)

    for person in database.accounts:
        if person.discord_id == discord_id:
            person.events.append(new_event)
            return

    new_account = Account(discord_id)
    new_account.events.append(new_event)
    database.accounts.append(new_account)

    return


bot.run(TOKEN)
