# Kurokami

Kurokami is a web scraper and live monitoring tool for the marketplace Carousell. Includes options such as price range
> [!NOTE]
> Support only for SG

> [!WARNING]
> Use this ethically as web scraping is heavily discouraged on this platform. Do not scrape more than needed.
> Once per 10 minutes is good enough

# Setup

Require python > 3.6 or you will be removing all the f strings in there

### Create the venv and install requirements in it
It is recommended that a venv is used in order to avoid conflict
```bash
python setup.py
```

### Activate the venv
On Linux:
```bash
source venv/bin/activate
```
to deactivate
```bash
deactivate
```

On Windows:
lazy to write this im doing it later

# Usage

### Kurokami Command line
```
usage: kurokami.py [-h] [-i ITEM] [-p PAGE] [-o OUTPUT] [-t] [-s] [-c COMPARE]

options:
  -h, --help            show this help message and exit
  -i ITEM, --item ITEM  Name of the item to scrape
  -p PAGE, --page PAGE  Number of pages (approx 46 per page)
  -o OUTPUT, --output OUTPUT
                        CSV file to write out to
  -t, --test            For debugging of parsers which could break often due to the changing structure, using a snapshot 
                        of a bs4 object while overriding these flags with the respective values: -i shirakami fubuki -p 1
  -s, --serialize       For debugging of parsers which could break often due to the changing structure, the BS4 object is serialised for fast access, must not have -t
  -c COMPARE, --compare Name of a .csv file output from this program
```

### Discord bot
```bash
python kurokami_bot.py
```
TODO: create daemon? make queries persist

For persistent monitoring, create a Discord [task](https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html) with `/create_thread item`

> [!WARNING]
> Running Kurokami currently blocks Discord API interactions when querying. This is because Kurokami is not asynchronous at the moment. Do not integrate Kurokami into your Discord bot if you require other features