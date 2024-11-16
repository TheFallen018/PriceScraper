import json
import os
import sys
import pathlib
from concurrent.futures import as_completed

import requests
from requests_futures.sessions import FuturesSession
from tqdm import tqdm


def get_working_proxies(refresh: bool = False):


    proxies = []

    print("No proxies found, fetching proxies from api.proxyscrape.com...")
    r = requests.get(
        "https://api.proxyscrape.com/?request=getproxies&proxytype=https&timeout=10000&country=all&ssl=all&anonymity=all")
    proxies += r.text.splitlines()
    r = requests.get(
        "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all")
    proxies += r.text.splitlines()
    working_proxies = []
    print(f"Checking {len(proxies)} proxies...")

    session = FuturesSession(max_workers=100)
    futures = []

    for proxy in proxies:
        future = session.get('https://api.myip.com', proxies={'https': f'http://{proxy}'}, timeout=5)
        future.proxy = proxy
        futures.append(future)

    for future in tqdm(as_completed(futures), total=len(futures)):  # , disable=True):
        try:
            future.result()
            working_proxies.append(future.proxy)
        except KeyboardInterrupt:
            sys.exit()
        except:
            continue

    with open("proxies.json", "w") as f:
        proxies = {"Proxies": working_proxies}
        proxies = json.dumps(proxies, indent=4)
        f.write(proxies)

    os.system("cls")

    return [None] + working_proxies

