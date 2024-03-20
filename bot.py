import discord
from discord.ext import commands
from pymongo import MongoClient
import io
import os
from dotenv import load_dotenv

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix="%%", intents=intents)

load_dotenv()

TOKEN = os.getenv("DC_BOT_TOKEN")
webhook_url = os.getenv('WEBHOOK_URL')
MONGO_SESSION = os.getenv("MONGO_SESSION")

db_name = "sonicmonitor"
collection_name = "sonic-mintokens-p"

# Mongo db Connection
mongo_client = MongoClient(MONGO_SESSION)
db = mongo_client[db_name]
collection = db[collection_name]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Use with caution haha
@bot.command()
@commands.has_permissions(administrator=True)
async def purge(ctx):  
    collection.delete_many({})
    await ctx.send("All data has been purged from the database.")

@bot.command()
async def add(ctx, *, text: str):
    # Attempt to split the input text into two parts: the word and its description
    parts = text.split(" ", 1)  # Splits the input into two parts at the first space
    
    word = parts[0]
    description = parts[1] if len(parts) > 1 else ""

    if not collection.find_one({"word": word}):
        collection.insert_one({"word": word, "description": description})
        response = f"**Added to the database: ** {word} - {description}"
    else:
        response = f"**{word} is already in the database.**"

    await ctx.send(response)

@bot.command()
async def remove(ctx, *, word: str):
    result = collection.delete_one({"word": word})
    if result.deleted_count > 0:
        await ctx.send(f"Removed '{word}' from the database.")
    else:
        await ctx.send(f"'{word}' not found in the database.")

@bot.command()
async def list(ctx):
    words = collection.find()
    # Creating a list of strings, each containing "word - description"
    words_and_descriptions = [f"{word['word']} - {word.get('description', 'No description provided')}" for word in words]
    
    response = "Words and Descriptions in the database:\n" + "\n".join(words_and_descriptions)
    
    max_length = 2000  # Discord's max message length
    if len(response) <= max_length:
        await ctx.send(response)
    else:
        # If the message is too long, send it as a file
        message_bytes = response.encode('utf-8')  # Encoding to bytes
        message_file = io.BytesIO(message_bytes)  # Creating a BytesIO object from the bytes
        message_file.seek(0)  # Seek to the start of the file
        await ctx.send(file=discord.File(fp=message_file, filename="words_and_descriptions_list.txt"))

# Run the bot
bot.run(TOKEN)