import discord
import datetime
import dotenv
import os
import threading
from requests import get
from json import loads
import asyncio

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

async def cat_fact(CHANNEL: int or discord.Channel = ""):
    print("invoke")
    await asyncio.sleep(1)
    try:
        catFact = loads(get("https://catfact.ninja/fact").content.decode("utf-8"))["fact"]
    except Exception as e:
        catFact = f"Meowerror: {e}"
    if CHANNEL == "":
        CHANNEL = client.get_channel(1216427363345371246)
    await CHANNEL.send(catFact)

@client.tree.command(description='Manually invoke')
@discord.app_commands.describe()
async def cat_fact(interaction: discord.Interaction):
    await cat_fact(interaction.channel)

async def run_blocking_task_in_thread():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, cat_fact)

if __name__ == "__main__":
    td = threading.Thread(target=asyncio.run, args=(run_blocking_task_in_thread(),))
    td.start()
    client.run(os.getenv('TOKEN'))