# BUG: Suppressed error while changing names

import discord
import datetime
import dotenv
import os
import threading
from requests import get
from json import loads
import asyncio
from typing import Union
import time
import sys
sys.path.append('..')
import kurokami

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.tasks = {}

    async def on_ready(self):
        print(f'{timestamp()}: Logged in as {client.user} (ID: {client.user.id})')

    def separate_thread(self, loop, query_delay, item_name, channel_id):
        # if asyncio.get_event_loop().is_running():
        #     # If a loop is already running, use it
        #     loop = asyncio.get_event_loop()
        # else:
        #     # If no loop is running, create a new one
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)
        asyncio.run_coroutine_threadsafe(self.cb(query_delay, item_name, channel_id), loop)
    
    async def cb(self, delay: int, item_name: str, channel_id: int):
        while True:
            s = time.time()
            await query_cb(item_name, channel_id)
            print(f"Time taken: {time.time() - s}")
            await asyncio.sleep(delay)

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

async def query_cb(item_name, channel_id, interaction = None):
    folder = today = datetime.datetime.now().strftime("%Y_%m_%d")
    timestamp = datetime.datetime.now().strftime("%H_%M_%S")
    new_filename = f'./output/{folder}/{timestamp}_{item_name}.csv'
    csv_files = []
    if not os.path.exists(f'./output/{folder}'):
        if not os.path.exists('./output'):
            os.makedirs('./output')
        else: # Possibly a new date
            os.makedirs(f'./output/{folder}') # create for today, after making a snapshot of before
    output_dir = './output/'
    all_folders = [name for name in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, name))]
    folder_dates = sorted([datetime.datetime.strptime(folder, "%Y_%m_%d").date() for folder in all_folders])
 
    while True: # Get the latest folder
        if len(folder_dates) == 0:
            print("No latest file found. Probably is the first time running this script, skipping comparison")
            folder = None
            break
        else:
            folder = str(folder_dates.pop(-1)).replace("-", "_")
            csv_files = [file for file in os.listdir(f'./output/{folder}') if file.endswith('.csv')]
            if len(csv_files) != 0:
                break
            elif folder != today:
                print(f"{folder} does not contain any CSV files, deleting")
                os.rmdir(f'./output/{folder}')
    if folder:
        folder = str(folder).replace("-", "_") # overwrite the current folder with the latest date known, for getting the last csv file
        sorted_files = sorted(csv_files)
        if sorted_files:
            last_file_path = os.path.join(f'./output/{folder}', sorted_files[-1])
        
        print(f"last file: {last_file_path}")
        new_results = kurokami.main({"i": item_name, "p": 1, "o": new_filename, "t": False, "s": False, "c": last_file_path})
    else:
        new_results = kurokami.main({"i": item_name, "p": 1, "o": new_filename, "t": False, "s": False})

    for result in new_results:
        seller_name, seller_url, item_name, item_img, item_url, time_posted, condition, price = result
        if len(price) == 1:
            price = price[0]
        else:
            price = f"{price[0]} ~~{price[1]}~~"
        try:
            catFact = loads(get("https://catfact.ninja/fact",timeout=10).content.decode("utf-8"))["fact"]
        except Exception as e:
            catFact = f"Meowerror: {e}"
        emb=discord.Embed(title=item_name, url=item_url, 
        description=f"# {price}\nPosted: {time_posted}\nSeller: [{seller_name}]({seller_url})\nCondition: {condition}", 
        color=0x00ff00) # timestamp=datetime.datetime.now()
        # emb.set_author(name=client.get_user(494483880410349595).name, icon_url=client.get_user(494483880410349595).display_avatar)
        emb.set_author(name="speckly")
        emb.set_footer(text=catFact)
        emb.set_image(url=item_img)
        if interaction:
            await interaction.followup.send_message(catFact)
        else:
            CHANNEL = client.get_channel(channel_id)
            await CHANNEL.send(embed=emb)

@client.tree.command(description='Manually invoke')
@discord.app_commands.describe()
async def cat_fact(interaction: discord.Interaction):
    await cat_fact_cb(interaction)

@client.tree.command(description='Create thread')
@discord.app_commands.describe(item="Name of the item to query", delay="Delay in seconds")
async def create_thread(interaction: discord.Interaction, item: str, delay: int):
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    else:
        cid = interaction.channel_id
        loop = asyncio.get_running_loop() 
        task = threading.Thread(target=client.separate_thread, args=[loop, delay, item, interaction.channel_id])
        # task = loop.create_task(client.cb(delay, item, interaction.channel_id)) # This uses one main, require full async
        await interaction.response.send_message(f"Created task with ```key: {item}``` in this channel")
        task.start()

        last_task = client.tasks.get(item)
        if last_task:
            await interaction.followup.send(f"Warning: this item ```{item}``` is being queried in channel {last_task['channel']}. This existing query will be cancelled")
            last_task['task'].cancel()
        for item in client.tasks:
            if client.tasks[item]["channel"] == cid:
                await interaction.followup.send(f"Warning: another item ```{item}``` is being queried in this channel. Consider terminating either query to avoid conflict")
        client.tasks[item] = {"task": task, "channel": cid}

@client.tree.command(description='View threads')
@discord.app_commands.describe()
async def view_threads(interaction: discord.Interaction):
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    elif client.tasks != {}:
        out_str = "\n".join([f"{item} in channel_id {client.tasks[item]['channel']}" for item in client.tasks])
        await interaction.response.send_message(out_str)
    else:
        await interaction.response.send_message("No tasks are running")
        
if __name__ == "__main__":
    client.run(os.getenv('TOKEN'))