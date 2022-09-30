import selenium
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import base64
import json
import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path

USE_PROXY = False

target_URLs = ['MAIN_URL_ROOT_DIRS', 
                'ANOTHER_URL_WITH_DIRS' ]

LOCAL_FOLDER = "./local_folder/"

chromeOptions = selenium.webdriver.ChromeOptions()

def get_soup(link):
    request_object = requests.get(link)
    soup = BeautifulSoup(request_object.content, features="lxml")
    return soup

# adapted code from 1st answer: https://stackoverflow.com/a/34631926
def find_internal_urls(internal_URL, depth=0, max_depth=2):
    print(internal_URL)
    url_objs = []
    soup = get_soup(internal_URL)
    a_tags = soup.findAll("a", href=True)

    if depth > max_depth:
        return {}
    else:
        for a_tag in a_tags:
            url_dict = {}
            if "Parent Directory" in str(a_tag):  # ignore links to parent directory
                continue
            elif "http" not in a_tag["href"] and "/" in a_tag["href"]:
                url = internal_URL + a_tag['href']
            else:
                url = a_tag["href"]
            url_dict["url"] = url
            url_dict["depth"] = depth + 1
            url_objs.append(url_dict)

    return url_objs


def filter_proxies():
    response = requests.get('https://www.sslproxies.org/')
    soup = BeautifulSoup(response.text,"html.parser")
    proxies = []
    for item in soup.select("table.table tbody tr"):
        if not item.select_one("td"):break
        ip = item.select_one("td").text
        port = item.select_one("td:nth-of-type(2)").text
        proxies.append(f"{ip}:{port}")
    return proxies

# possible solutions for getting a list of PROXIES --> https://gist.github.com/tushortz/cba8b25f9d80f584f807b65890f37be5
def create_proxy_driver(PROXY):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    if USE_PROXY:
        options.add_argument(f'--proxy-server={PROXY}')
    driverExePath = "./drivers/chromedriverWin.exe"
    if os.name != 'nt':
        driverExePath = "./drivers/chromedriver"
    print(driverExePath)
    driver = selenium.webdriver.Chrome(options=options, executable_path=driverExePath)
    return driver

if USE_PROXY:
    print('Selenium opens headless browser... (with Proxy)')
else:
    print('Selenium opens headless browser...')
# creating new driver to use proxy
ALL_PROXIES = filter_proxies()
proxydriver = create_proxy_driver(ALL_PROXIES)

#proxydriver = selenium.webdriver.Chrome(options=chromeOptions) 

def save_file(download_url, downloaded_file, projectFolder):

    filename = download_url.split("/")[-1]
    print('Saving file to local folder:', filename)
    Path(LOCAL_FOLDER + projectFolder).mkdir(parents=True, exist_ok=True)
    fp = open(LOCAL_FOLDER + projectFolder + filename, 'wb')
    # TODO: save hashcode checksum of the downloaded_file and next time check if it's already downloaded
    fp.write(base64.b64decode(downloaded_file))
    fp.close()

def save_downloaded(download_url):

    fp = open("saved_before.txt", 'a')
    fp.write(download_url+"\n")
    fp.close()

def load_downloaded():

    fp = open("saved_before.txt", 'r')
    urls = fp.readlines()
    fp.close()
    return urls



for target_url in target_URLs:
    proxydriver.get( target_url )
    print("Checking directory with url:", target_url)
    time.sleep(3)

    if "<html><head></head><body></body></html>" in proxydriver.page_source or \
         "ERR_NO_SUPPORTED_PROXIES" in proxydriver.page_source:
        print("PROBLEM: PROXIES ARE NOT SUPPORTED IN THIS PAGE!")
        continue

    scraped_URLs = []
    elems = proxydriver.find_elements(By.XPATH, "//a[@href]")
    for elem in elems:
        #print(elem.get_attribute("href"))
        directoryURL = elem.get_attribute("href")
        if directoryURL.endswith("/"):
            print("Finding internal urls of", directoryURL)
            internal_urls = find_internal_urls(directoryURL)
            print("URLS found:")
            for internal in internal_urls:
                dirName = elem.text # name of the directory to be created in local file-structure
                url_obj = {"dir":dirName, "url": internal["url"], "dirURL": directoryURL }
                print(url_obj)
                scraped_URLs.append(url_obj)

    # visit the internal URLs (directories) and download any file
    for url_obj in scraped_URLs:
        proxydriver.get( url_obj["dirURL"] )
        time.sleep(1)
        download_url = url_obj["url"]

        previously_saved = load_downloaded()
        if (url_obj["dirURL"] + download_url+"\n") in previously_saved or \
            download_url.endswith("/"):
            continue

        print('Injecting retrieval code into web page')
        proxydriver.execute_script("""
            window.file_contents = null;
            var xhr = new XMLHttpRequest();
            xhr.responseType = 'blob';
            xhr.onload = function() {
                var reader  = new FileReader();
                reader.onloadend = function() {
                    window.file_contents = reader.result;
                };
                reader.readAsDataURL(xhr.response);
            };
            xhr.open('GET', %(download_url)s);
            xhr.send();
        """.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ') % {
            'download_url': json.dumps(download_url),
        })

        print('Looping until file is retrieved')
        downloaded_file = None
        while downloaded_file is None:
            # Returns the file retrieved base64 encoded (perfect for downloading binary)
            downloaded_file = proxydriver.execute_script('return (window.file_contents !== null ? window.file_contents.split(\',\')[1] : null);')
            #print(downloaded_file)
            if not downloaded_file:
                print('\tNot downloaded, waiting...')
                time.sleep(1.5)
        try:
            if "DOCTYPE html" in base64.b64decode(downloaded_file).decode():
                continue
        except:
            pass
        print('\tDone')

        save_file(download_url, downloaded_file, url_obj["dir"])

        save_downloaded(url_obj["dirURL"]+download_url)

        print('\tDone')

proxydriver.close() # close web browser before exit