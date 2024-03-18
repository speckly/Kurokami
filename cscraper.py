from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
import urllib
from pprint import pprint
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pickle
import traceback
import argparse

def request_page(url):
    """ Returns BeautifulSoup4 Objects (soup)"""
    driver.get(url)
    page = 1
    timeout = 5
    while page < page_limit:
        try:
            next_page_btn = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, '//main[1]/div/button[.="Load more"]')))  # wait max timeout sec for loading
            driver.execute_script("arguments[0].click();", next_page_btn)  # click the load more button through ads
            page += 1
        except TimeoutException as e:
            break
    time.sleep(timeout)
    print(f'All results loaded. Total: {page} pages.')
    return BeautifulSoup(driver.page_source, "html.parser")


def parse_info(item_div, mode=1):
    a = item_div.find_all('a', recursive=False)
    seller_divs = a[0].find_all('div', recursive=False)[1]
    item_p = a[1].find_all('p', recursive=False)
    if mode == 1:
        return {'seller_name': seller_divs.p.get_text(),
                'seller_url': home+a[0]['href'],
                'item_name': a[1].find_all('div', recursive=False)[1].p.get_text(),
                'item_url': home+a[1]['href'],
                'time_posted': seller_divs.div.p.get_text(),  # TODO: process into absolute datetime
                'condition': item_p[1].get_text(),
                'price': re.findall(r"\$\d+", "".join([p.get_text().replace(',', '') for p in item_p]))
                }  # 0 is discounted price, 1 is original price, if applicable
    else:
        return {'seller_name': seller_divs.p.get_text(),
                'seller_url': home+a[0]['href'],
                'item_name': item_p[0].get_text(),
                'item_url': home+a[1]['href'],
                'time_posted': seller_divs.div.p.get_text(),  # TODO: process into absolute datetime
                'condition': item_p[3].get_text(),
                'price': re.findall(r"\d+", item_p[1].get_text().replace(',', ''))[0]}  # 0 is discounted price, 1 is original price, if applicable

if __name__ == "__main__":
    ps = argparse.ArgumentParser()
    ps.add_argument('-i', '--item', type=str, help='Name of the item to scrape')
    ps.add_argument('-p', '--page', type=int, help='Number of pages (approx 50 per page)')
    ps.add_argument('-o', '--output', type=str, help='CSV file to write out to')
    ps.add_argument('-t', '--test', action='store_true', help=r'''For debugging of parsers which could break often due to the changing structure, 
        using a snapshot of a bs4 object while overriding these flags with the respective values: -i shirakami fubuki -p 1''')
    args = ps.parse_args()
    print("Author: Andrew Higgins")
    print("https://github.com/speckly")
    print("Creating webdriver")
    
    if args.item:
        item = args.page
    else:
        item = input('Up to how many pages to scrap? Each page is 23-25 listings: ')
    if args.page:
        page_limit = args.page
    else: 
        while True:
            inp = input('Number of pages (approx 50 per page): ')
            if inp.isdigit():
                page_limit = int(inp)
                break
            else:
                print("Invalid integer")
    if args.output:
        if not re.match(r'^[a-zA-Z0-9_\-]+\.csv$', args.output):
            output_file = args.output
        else:
            print("Invalid CSV file name. Please provide a name consisting of letters, numbers, underscores, and dashes, ending with .csv")
            exit()
    else:
        while True:
            inp = input('Enter the name for the CSV file: ')
            if re.match(r'^[a-zA-Z0-9_\-]+\.csv$', inp):
                csv_filename = inp
                break
            else:
                print("Invalid CSV file name. Please provide a name consisting of letters, numbers, underscores, and dashes, ending with .csv")
    if args.test:
        item = 'shirakami fubuki'
        page_limit = 1
        if args.item or args.page:
            print('Entered test mode, overriding some user provided arguments with -i shirakami fubuki -p 1') 

    home = 'https://sg.carousell.com'
    subdirs = f'/search/{urllib.parse.quote(item)}'
    parameters = f'?addRecent=false&canChangeKeyword=false&includeSuggestions=false&sort_by=3'
    opts = Options()
    opts.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    driver = webdriver.Chrome(options=opts)
    driver.minimize_window()
    print(f'Chrome Web Driver loaded. Version: {driver.capabilities["browserVersion"]}\n')  # use "version" on Linux
    
    try:
        print(f'Retrieving search results on {item}...')
        search_results_soup = request_page(home+subdirs+parameters)
        # with open("soup.pkl", "rb") as f:
        #     search_results_soup = pickle.load(f)
        # Strip down
        browse_listings_divs = search_results_soup.find(class_="asm-browse-listings")
        item_divs_class = browse_listings_divs.select_one('.asm-browse-listings > div > div > div > div > div')['class']

        print(f'Detected item_divs class: {item_divs_class}')
        item_divs = search_results_soup.find_all('div', class_=item_divs_class)  # filter out ads divs
        print(f'Found {len(item_divs)} listings. Parsing...')
    except AttributeError as e:  # no item_divs at all
        raise RuntimeError('The search has returned no result.')

    parse_mode = 1
    tries = 1
    while tries < 5:  # retrying loop as the div class position is random
        try:
            items_list = []
            for item_div in item_divs:
                items_list.append(parse_info(item_div, parse_mode)) 
            break
        except IndexError as e:
            print(traceback.format_exc())
            print(f'Parsing attempt {tries} failed due to class name error using parse mode {parse_mode}. Retrying with parse mode 2...\n')
            tries += 1
            parse_mode = 2
            continue
    else:
        raise RuntimeError('Parsing failed as it still faces IndexError after 5 tries.')

    driver.quit()
    print(f'Parse success using mode {parse_mode}! Sample item parsed:')
    pprint(items_list[0])
    df = pd.DataFrame(items_list)
    df.to_csv(f'{item}.csv', index=False)
    print(f'Results saved to {item}.csv')
    input('Press enter to exit ')

'''
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
