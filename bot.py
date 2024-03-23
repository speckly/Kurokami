import discord
import datetime
import dotenv
import os
import threading
from requests import get
from json import loads
import asyncio
import time
from typing import Union

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        MY_GUILD = discord.Object(id=1093515712900902912)
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
    

dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
client = MyClient(intents=intents)

def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@client.event
async def on_ready():\
    print(f'{timestamp()}: Logged in as {client.user} (ID: {client.user.id})')

async def cat_fact_cb(interaction = None):
    print("invoke")
    
    try:
        catFact = loads(get("https://catfact.ninja/fact").content.decode("utf-8"))["fact"]
    except Exception as e:
        catFact = f"Meowerror: {e}"
    if interaction:
        await interaction.response.send_message(catFact)
    else:
        CHANNEL = client.get_channel(1216427363345371246)
        await CHANNEL.send(catFact)

@client.tree.command(description='Manually invoke')
@discord.app_commands.describe()
async def cat_fact(interaction: discord.Interaction):
    await cat_fact_cb(interaction)

async def cb(delay: int):
    await asyncio.sleep(delay)
    await cat_fact_cb()

if __name__ == "__main__":
    td = threading.Thread(target=cb, args=(10,))
    td.start()
    client.run(os.getenv('TOKEN'))