'''
Author: Andrew Higgins
https://github.com/speckly

Two parse modes only differs in item divs 2nd a
Structure of Carousell HTML FORMAT 1 (parse_mode 1):
body > find main > 1st div > 1st div > divs of items
    in divs of items > parents of each item
        parent > 1st div > 1st a is seller, 2nd a is item page
            in 1st a: 2nd div > p is seller name, > div > p is time posted
            in 2nd a: 2nd div > p is item name but with ... if too long, directly under 2nd a first p is price, 2nd p is condition
        parent > 2nd div > button > span is number of likes
total 24 or 25 results loaded once.

Structure of Carousell HTML FORMAT 2 (parse_mode 2):
body > find main > 1st div > 1st div > divs of items
    in divs of items > parents of each item
        parent > 1st div > 1st a is seller, 2nd a is item page
            in 1st a: 2nd div > p is seller name, > div > p is time posted
            in 2nd a: 1st p is FULl NAME, 2nd p is price, 3rd p is description, 4th p is condition
        parent > 2nd div > button > span is number of likes
total 24 or 25 results loaded once.

body > find main > div > button to view more
view more button loads on top of existing, so can prob spam view more then gather all items at once
MAY NOT BE FIRST DIV! Temp workaround is to get class name of the correct item divs

My way:
.asm-browse-listings > div > div > div of item > div with testid > div of item stripped
'''

from typing import Union
import pickle
import traceback
import argparse
import os
import asyncio
import re
import urllib
import sys
from pprint import pprint
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

async def request_page(url, page_limit):
    """ Returns BeautifulSoup4 Objects (soup)"""

    opts = Options()
    opts.add_argument("--log-level=3")
    # opts.add_argument("--headless") # Requires human verification
    opts.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    driver = webdriver.Chrome(options=opts)
    driver.minimize_window()

    driver.get(url)
    page = 1
    timeout = 10

    while page < page_limit:
        try:
            next_page_btn = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Show more results")]')))  # wait max timeout sec for loading
            driver.execute_script("arguments[0].click();", next_page_btn)  # click the load more button through ads
            page += 1
        except TimeoutException:
            print("Button not found, reached end of page or load more button not found.")
            break

    pg = driver.page_source
    driver.quit()
    return BeautifulSoup(pg, "html.parser")


def parse_info(item_div, home, mode=1):
    """Author: Andrew Higgins
    https://github.com/speckly

    Parses the item_div and returns the list of items
    """
    a = item_div.find_all('a', recursive=False)
    seller_divs = a[0].find_all('div', recursive=False)[1]
    item_p = a[1].find_all('p', recursive=False)
    img = item_div.find('img')
    if mode == 1:
        return {'seller_name': seller_divs.p.get_text(),
                'seller_url': home+a[0]['href'],
                'item_name': img['title'] if img else "Title not found as this is a video",
                'item_img': img['src'] if img else None,
                'item_url': home+a[1]['href'],
                'time_posted': seller_divs.div.p.get_text(),  # Attempt to get absolute datetime?
                'condition': item_p[1].get_text(),
                'price': re.findall(r"\$\d{0,3},?\d+\.?\d{,2}", a[1].get_text())
                }  # 0 is discounted price, 1 is original price, if applicable
    else:
        return {'seller_name': seller_divs.p.get_text(),
                'seller_url': home+a[0]['href'],
                'item_name': item_p[0].get_text(),
                'item_url': home+a[1]['href'],
                'time_posted': seller_divs.div.p.get_text(),
                'condition': item_p[3].get_text(),
                'price': re.findall(r"\d+", item_p[1].get_text().replace(',', ''))[0]}

async def main(options: Union[dict, None] = None):
    """options keys: i (item), p (page), o (output), t (test), s (serialize), c (compare)"""
    if options is None:
        server_side = False
        ps = argparse.ArgumentParser()
        ps.add_argument('-i', '--item', type=str, help='Name of the item to scrape')
        ps.add_argument('-p', '--page', type=int, help='Number of pages (approx 46 per page)')
        ps.add_argument('-o', '--output', type=str,
            help='CSV file to write out to, defaults to timestamped')
        ps.add_argument('-t', '--test', action='store_true',
            help=r'''For debugging of parsers which could break often due to the changing structure,
            using a snapshot of a bs4 object while overriding these flags with the respective values: -i shirakami fubuki -p 1''')
        ps.add_argument('-s', '--serialize', action='store_true',
            help=r'''For debugging of parsers which could break often due to the changing structure,
            the BS4 object is serialised for fast access, must not have -t''')
        ps.add_argument('-c', '--compare', type=str,
            help='Name of a .csv file output from this program')
        args = ps.parse_args()

        if args.test:
            test = True
            item = 'test'
            page_limit = 1
            if args.item or args.page:
                print('Entered test mode, overriding some user provided arguments')
        else:
            test = False
            if args.item:
                item = args.item
            else:
                item = input('-i Item name: ')
            if args.page:
                page_limit = args.page
            else:
                while True:
                    inp = input('-p Number of pages (approx 50 per page): ')
                    if inp.isdigit():
                        page_limit = int(inp)
                        break
                    else:
                        print("Invalid integer")
        file_reg = r'^.?[a-zA-Z0-9_\\/\-]+\.csv$'
        output_file = args.output
        if output_file:
            if not re.match(file_reg, output_file):
                print("Invalid CSV file name. Please provide a name consisting of letters, numbers, underscores, and dashes, ending with .csv")
                sys.exit(1)
            elif not os.path.exists(output_file):
                print(f"{output_file} does not exist")
                sys.exit(1)
        else:
            print("Using default csv file format")
            output_file = item + ".csv"

        serialize = args.serialize
        compare_file = args.compare
        if compare_file:
            if not re.match(file_reg, args.compare):
                print(f"Invalid CSV file name {compare_file}. Please provide a name consisting of letters, numbers, underscores, and dashes, ending with .csv")
                sys.exit(1)
            elif not os.path.exists(compare_file):
                print(f"{compare_file} does not exist")
                sys.exit(1)

    else: # Praying that this does not result in a SSRF, used in bot.py with no user inputs yet. Validate user inputs
        server_side = True
        item = options.get("i")
        output_file = options.get("o")
        page_limit = options.get("p")
        if options.get("t"):
            test = True
            item = 'shirakami fubuki'
            page_limit = 1
        else:
            test = False
        serialize = options.get("s")
        compare_file = options.get("c")

    if not server_side:
        print("Author: Andrew Higgins")
        print("https://github.com/speckly")

    home = 'https://sg.carousell.com'
    subdirs = f'/search/{urllib.parse.quote(item)}'
    parameters = '?addRecent=false&canChangeKeyword=false&includeSuggestions=false&sort_by=3'

    try:
        if not server_side:
            print(f'Retrieving search results on {item}...')
        if not test:
            if not server_side:
                print("Creating webdriver")
            search_results_soup = await request_page(home+subdirs+parameters, page_limit=page_limit)
            if not server_side:
                print(f'All results loaded. Total: {page_limit} pages.')
            if serialize:
                with open("./utils/soup.pkl", "wb") as f:
                    pickle.dump(search_results_soup, f)
                print(f"Serialized: -i {item}")
        else:
            with open("./utils/soup.pkl", "rb") as f:
                search_results_soup = pickle.load(f)
        # Strip down
        browse_listings_divs = search_results_soup.find(class_="asm-browse-listings")
        item_divs_class = browse_listings_divs.select_one('.asm-browse-listings > div > div > div > div > div')['class']
        if not server_side:
            print(f'Detected item_divs class: {item_divs_class}')
        item_divs = search_results_soup.find_all('div', class_=item_divs_class)  # ads
        if not server_side:
            print(f'Found {len(item_divs)} listings. Parsing...')
    except AttributeError:  # no item_divs at all
        raise RuntimeError('The search has returned no result.')

    parse_mode = 1
    tries = 1
    while tries < 5:  # retrying loop as the div class position is random
        try:
            items_list = []
            for item_div in item_divs:
                items_list.append(parse_info(item_div, home, parse_mode))
            break
        except IndexError:
            print(traceback.format_exc())
            print(f'Parsing attempt {tries} failed due to class name error using parse mode {parse_mode}. Retrying with parse mode 2...\n')
            tries += 1
            parse_mode = 2
            continue
    else:
        raise RuntimeError('Parsing failed as it still faces IndexError after 5 tries.')

    df = pd.DataFrame(items_list)
    df.to_csv(output_file, index=False)
    if not server_side:
        print(f'Parse success using mode {parse_mode}! Sample item parsed:')
        pprint(items_list[0])
        print(f'Results saved to {output_file}')

    if compare_file:
        prev_df = pd.read_csv(compare_file)
        df_standardized = df.iloc[:len([prev_df])] # cases where there might be extra old results appended to new df, remove these
        new_rows = df_standardized[~df_standardized['item_name'].isin(prev_df['item_name'])]
        return new_rows.values.tolist() # TODO: use dict
    else:
        return df.values.tolist()

if __name__ == "__main__":
    compare_results = asyncio.run(main())
    if compare_results:
        print(f"The difference between the previous and this query is {compare_results}")
        print(f"There are {len(compare_results)} new listings")
