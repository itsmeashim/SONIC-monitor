import requests
import json
import time
import os
from pymongo import MongoClient
import random
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()


DC_TOKEN = os.getenv("DC_TOKEN")
webhook_url = os.getenv('WEBHOOK_URL')
MONGO_SESSION = os.getenv("MONGO_SESSION")

db_name = "sonicmonitor"
collection_name = "sonic-mintokens-p"

#tokos
SONIC_ID = os.getenv("SONIC_ID")
guild_id = os.getenv("guild_id")

# Mongo db Connection
mongo_client = MongoClient(MONGO_SESSION)
db = mongo_client[db_name]
collection = db[collection_name]

def get_response(channel_id):
    data_reversed = []
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    header = {
        'authorization': DC_TOKEN
    }
    response = requests.get(url, headers=header).json()
    if isinstance(response, list):
        data_reversed = response[::-1]
    return data_reversed

def process_message(message):
    try:
        embeds = message.get('embeds', [{}])
        embed = embeds[0] if len(embeds) > 0 else {}

        if not embed:
            return ""

        message_title = embed.get('title', "")
        message_desc = embed.get("description", "")
        message_fields = embed['fields']
        print(f"Message title: {message_title}")
        logging.info(f"Message title: {message_title}")

        fields_values = [list(field.values()) for field in message_fields]
        message_content = f"{message_title}{message_desc}{str(fields_values)}"
        message_content = message_content.lower().replace(")", " ").replace("(", " ").replace(",", "").replace("'", " ").replace("[", " ").replace("]", " ").replace("◎", " ").replace("\n", " ").replace("*", " ").replace("\x00"," ")
        return message_content
    except Exception as e:
        print(f"Error: {e}")
        return ""

def send_alert_to_discord(guild_id, channel_id, message_id, embed, triggered_words_with_descriptions):
    link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
    description_lines = [f"- **{item['word']}**: {item['description']}" for item in triggered_words_with_descriptions]
    description_text = "\n".join(description_lines)

    embed_pd = {
        "title": "Trigger word found!",
        "description": f"Trigger Words and Descriptions:\n{description_text}",
        "url": link
    }

    data = {
        "embeds": [embed_pd, embed]
    }
    requests.post(webhook_url, json=data)

def check_response(response, prev_id, latest_message_id, channel_id):
    try:
        latest_message = response
        prev_id = latest_message_id if not prev_id else prev_id
        new_id = int(latest_message['id'])

        if int(prev_id) < int(new_id):
            message_content = process_message(latest_message)
            embeds = latest_message.get('embeds', [{}])
            embed = embeds[0] if len(embeds) > 0 else {}

            if not embed:
                return new_id

            # Fetch trigger words and descriptions from MongoDB
            triggers = list(collection.find({}, {'_id': 0, 'word': 1, 'description': 1}))
            trigger_words = [doc['word'].lower() for doc in triggers]
            
            message_content_array = message_content.lower().split(" ")
            message_content_array = [word for word in message_content_array if word]  # Remove empty strings

            triggered = []
            for trigger in triggers:
                if trigger['word'].lower() in message_content_array:
                    triggered.append({"word": trigger['word'], "description": trigger.get('description', 'No description provided')})

            if triggered:
                send_alert_to_discord(guild_id, channel_id, new_id, embed, triggered)

            return new_id
    except Exception as e:
        print(f"Error: {e}")
    return prev_id

if __name__ == "__main__":
    i = 0
    mint_token_prev_id = 0
    while True:
        try:
        # Increment check count and print status
            i += 1
            print(f"Checking Now, times checked: {i}")
            logging.info(f"Checking Now, times checked: {i}")

            # Fetch messages from Discord
            mint_token_response = get_response(SONIC_ID)

            for response in mint_token_response:
                latest_message_id = mint_token_response[-1]['id']
                mint_token_new_id = check_response(response, mint_token_prev_id, latest_message_id, SONIC_ID)
                mint_token_prev_id = mint_token_new_id if mint_token_new_id else mint_token_prev_id
        except Exception as e:
            print(f"Error: {e}")
            continue
        if not i == 1:
            time.sleep(random.uniform(25, 30))