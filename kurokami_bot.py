"""Author: Andrew Higgins
https://github.com/speckly

Project Kurokami: Discord Bot with Slash Commands for remote usage
BUG: Suppressed error while changing names
"""

import os
from datetime import datetime
import time
import sys
import asyncio
import json

import discord
from discord.ext import tasks
import dotenv
import aiohttp

sys.path.append('..')
import kurokami

class Query():
    """
    Author: Andrew Higgins
    https://github.com/speckly
    
    This class is responsible for using Kurokami and handling its data"""
    def __init__(self, name: str, cid: int, delay: float, mn: float, mx: float):
        self.name = name
        self.channel = cid
        self.delay = delay
        self.cb = tasks.loop(seconds=delay)(self._cb_impl)
        self.min = mn # Min
        self.max = mx # Max

    def __repr__(self):
        return f"<Query name:{self.name} channel:{self.channel} delay:{self.delay} min:{self.min} max:{self.max}>"

    def __str__(self):
        return f"Name: {self.name}, Channel: {self.channel}, Delay: {self.delay}, Min: {self.min}, Max: {self.max}"

    async def _cb_impl(self):
        s = time.time()
        await self._query_cb()
        print(f"{self.name}, time taken: {time.time() - s}")

    async def _query_cb(self):
        """Author: Andrew Higgins
        https://github.com/speckly
        
        Slash command, views the list of Query objects"""
        item_name = self.name
        folder = today = datetime.now().strftime("%Y_%m_%d")
        timestamp = datetime.now().strftime("%H_%M_%S")
        new_filename = f'./output/{folder}/{timestamp}_{item_name}.csv'
        csv_files = []
        if not os.path.exists(f'./output/{folder}'):
            if not os.path.exists('./output'):
                os.makedirs('./output')
            else: # Possibly a new date
                os.makedirs(f'./output/{folder}') # create for today, after making a snapshot of before
        output_dir = './output/'
        all_folders = [name for name in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, name))]
        folder_dates = sorted([datetime.strptime(folder, "%Y_%m_%d").date() for folder in all_folders])

        while True: # Get the latest folder
            if len(folder_dates) == 0:
                pages = 20
                print("No latest file found. Probably is the first time running this script, skipping comparison")
                folder = None
                break
            pages = 1
            folder = str(folder_dates.pop(-1)).replace("-", "_")
            csv_files = [file for file in os.listdir(f'./output/{folder}') if file.endswith(f'{item_name}.csv')]
            if len(csv_files) != 0:
                break
            if folder != today:
                print(f"Note: {folder} does not contain any CSV files")

        # TODO: Observe
        if folder: # overwrite the current folder with the latest date known, for getting the last csv file
            folder = str(folder).replace("-", "_")
            sorted_files = sorted(csv_files)
            if sorted_files:
                last_file_path = os.path.join(f'./output/{folder}', sorted_files[-1])

            new_results = await kurokami.main({"i": item_name, "p": pages, "o": new_filename, "t": False, "s": False, "c": last_file_path})
        else:
            new_results = await kurokami.main({"i": item_name, "p": pages, "o": new_filename, "t": False, "s": False})

        print(new_results)
        for result in new_results:
            seller_name, price, time_posted, condition, item_name, item_url, item_img, seller_url = result[1:] # exclude UID

            current_price = float(price[0].replace("$", "").replace(",", "").replace("FREE", "0"))
            if self.min < current_price < self.max:
                if len(price) == 1: # Trim down
                    price = price[0]
                else:
                    price = f"{price[0]} ~~{price[1]}~~"
                cat_fact = await fetch_cat_fact()
                emb=discord.Embed(title=item_name, url=item_url,
                description=f"""# {price}
Posted: {time_posted}
Seller: [{seller_name}]({seller_url})
Condition: {condition}""",
                color=0x00ff00) # timestamp=datetime.now()
                try:
                    emb.set_author(name=client.get_user(494483880410349595).name,
                        icon_url=client.get_user(494483880410349595).display_avatar)
                except AttributeError:
                    print("Get user failed")
                    emb.set_author(name="New item")
                emb.set_footer(text=cat_fact)
                emb.set_image(url=item_img)
                channel = client.get_channel(self.channel)
                await channel.send(embed=emb)

class MyClient(discord.Client):
    """Author: Andrew Higgins
    https://github.com/speckly
    
    TODO: Use commands.Bot which is painful to transition to
    
    Client object for Discord"""
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.tasks = {}

    async def on_ready(self):
        """Author: Andrew Higgins
        https://github.com/speckly"""
        print(f'{_timestamp()}: Logged in as {client.user} (ID: {client.user.id})')
        with open("queries.json", encoding="utf-8") as queries_file:
            queries = json.load(queries_file)
        for name, query_params in queries.items():
            print(f"Resuming query {name}, params: {query_params}")
            thread = Query(*query_params.values()) # file is sorted as vars returns in order
            thread.cb.start()
            self.tasks[name] = thread

    async def setup_hook(self):
        my_guild = discord.Object(id=1093515712900902912)
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
client = MyClient(intents=intents)

def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def fetch_cat_fact() -> str:
    """Author: Andrew Higgins
    https://github.com/speckly
    
    Returns cat fact from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://catfact.ninja/fact", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    cat_fact = data["fact"]
                else:
                    cat_fact = f"Meowerror: HTTP status {response.status}"
    except aiohttp.ClientError as e:
        cat_fact = f"Meowerror: {e}"
    return cat_fact

@client.tree.command(description='Create thread for monitoring')
@discord.app_commands.describe(item="Name of the item to query", delay="Delay in seconds", mn="Minimum price to send an embed", mx="Maxmimum price to send an embed")
async def create_thread(interaction: discord.Interaction, item: str, delay: int, mn: str = "0", mx: str = "999999"):
    """Author: Andrew Higgins
    https://github.com/speckly
    
    Slash command, creates a new Query object that constantly scrapes off Carousell with the given arguments
    """
    if not mn.isdigit() or not mx.isdigit():
        await interaction.response.send_message("Input is not a float")
    else:
        mn = float(mn)
        mx = float(mx)
    if mn < 0:
        await interaction.response.send_message("Min must be equal or greater than 0")
    if not mx > mn:
        await interaction.response.send_message("Max must be greater than the min")
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    else:
        await interaction.response.send_message(f"Creating thread: {item}")
        cid = interaction.channel_id
        thread = Query(name=item, cid=cid, delay=delay, mn=mn, mx=mx)
        thread.cb.start()

        last_task = client.tasks.get(item)
        if last_task:
            await interaction.followup.send(f"Warning: this thread ```{item}``` exists in channel {last_task.channel}. This existing query will be cancelled")
            last_task.cb.cancel()
        for item_name, query in client.tasks.items():
            if query.channel == cid:
                await interaction.followup.send(f"Warning: another thread ```{item_name}``` uses this channel. Consider terminating either to avoid conflict")
        client.tasks[item] = thread
        await interaction.followup.send(content=f"{item} thread created successfully")

@client.tree.command(description='View threads')
async def view_threads(interaction: discord.Interaction):
    """Author: Andrew Higgins
    https://github.com/speckly
    
    Slash command, views the list of Query objects"""
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    elif client.tasks:
        out_str = "\n".join([f"{name} in channel_id {query.channel}, every {query.delay} seconds. ${query.min}~${query.max}" for name, query in client.tasks.items()])
        await interaction.response.send_message(out_str)
    else:
        await interaction.response.send_message("No tasks are running")

@client.tree.command(description='Stop thread')
@discord.app_commands.describe(name='Name of the thread to stop, must be existing, get list of threads with /view_threads')
async def delete_thread(interaction: discord.Interaction, name: str=''):
    """Author: Andrew Higgins
    https://github.com/speckly
    
    Slash command, views the list of Query objects"""
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    elif name == '':
        await interaction.response.send_message("Missing item name, stopping all current threads in this channel instead")
        cid = interaction.channel_id
        for name, stored_item in client.tasks.items():
            if stored_item.channel == cid:
                stored_item.cb.cancel()
                del client.tasks[name]
                await interaction.followup.send(f"Stopped thread {name} located in current channel")
                break

    else:
        thread = client.tasks.get(name)
        if thread:
            thread.cb.cancel()
            await interaction.response.send_message(f"Thread {name} stopped successfully")
            del client.tasks[name]
        else:
            await interaction.response.send_message(f"Thread {name} does not exist. View list of threads with /view_threads")


async def main():
    """Author: Andrew Higgins
    https://github.com/speckly
    
    Main function of Kurokami bot"""
    await client.login(os.getenv('TOKEN'))
    await client.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down Kurokami")
        with open("queries.json", "w", encoding="utf-8") as q_file:
            json.dump({name:{attr:val for attr, val in vars(query).items() if attr != "cb"} for name, query in client.tasks.items()} ,q_file, indent=4)
