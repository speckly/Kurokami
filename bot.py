import discord
import datetime
import dotenv
import os
import threading
from requests import get
from json import loads
import asyncio
from typing import Union

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'{timestamp()}: Logged in as {client.user} (ID: {client.user.id})')
        loop = asyncio.get_running_loop() 
        threading.Thread(target=self.separate_thread, args=[loop]).start()

    def separate_thread(self, loop):
        asyncio.run_coroutine_threadsafe(self.cb(60), loop)
    
    async def cb(self, delay: int):
        while True:
            await asyncio.sleep(delay)
            await cat_fact_cb()

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

async def cat_fact_cb(interaction = None):
    try:
        catFact = loads(get("https://catfact.ninja/fact").content.decode("utf-8"))["fact"]
    except Exception as e:
        catFact = f"Meowerror: {e}"
    if interaction:
        await interaction.response.send_message(catFact)
    else:
        CHANNEL = client.get_channel(1093515713366478953)
        await CHANNEL.send(catFact)

@client.tree.command(description='Manually invoke')
@discord.app_commands.describe()
async def cat_fact(interaction: discord.Interaction):
    await cat_fact_cb(interaction)

if __name__ == "__main__":
    client.run(os.getenv('TOKEN'))