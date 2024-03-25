# Kurokami

Kurokami is a web scraper and live monitoring tool for the marketplace Carousell. 
> [!NOTE]
> Support only for SG

> [!WARNING]
> Use this ethically as web scraping is heavily discouraged on this platform. Do not scrape more than needed.
> Once per 10 minutes is good enough

# Usage

```
usage: cscraper.py [-h] [-i ITEM] [-p PAGE] [-o OUTPUT] [-t]
```

options:
  -h, --help            show this help message and exit
  -i ITEM, --item ITEM  Name of the item to scrape
  -p PAGE, --page PAGE  Number of pages (approx 50 per page)
  -o OUTPUT, --output OUTPUT
                        CSV file to write out to
  -t, --test            For debugging of parsers which could break often due to the changing structure, using a snapshot of a bs4 object with -i shirakami fubuki -p 1
