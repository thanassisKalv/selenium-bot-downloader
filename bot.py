import pyvirtualdisplay
import selenium
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import base64
import json

LOCAL_FOLDER = "./local_folder/"

# TODO: we use a hardcoded list of target URLs (directories), get them dynamically if root folder has children directories
target_URLs = ['https://archive.ics.uci.edu/ml/machine-learning-databases/liver-disorders/',
                "https://archive.ics.uci.edu/ml/machine-learning-databases/ipums-mld/"]

chromeOptions = selenium.webdriver.ChromeOptions()
#prefs = {"download.default_directory" : "./test"}
#chromeOptions.add_experimental_option("prefs",prefs)

chromeOptions.add_argument("--disable-extensions")
chromeOptions.add_argument("--disable-gpu")
chromeOptions.add_argument("--headless")

print('Selenium opens headless browser...')
driver = selenium.webdriver.Chrome(options=chromeOptions) 

def save_file(download_url):

    filename = download_url.split("/")[-1]
    print('Saving file to local folder:', filename)
    fp = open(LOCAL_FOLDER + filename, 'wb')
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
    driver.get( target_url )
    print("Checking directory:", target_url)
    time.sleep(1)

    scraped_URLs = []
    elems = driver.find_elements(By.XPATH, "//a[@href]")
    for elem in elems:
        #print(elem.get_attribute("href"))
        scraped_URLs.append(elem.get_attribute("href"))

    for download_url in scraped_URLs:

        previously_saved = load_downloaded()
        if (download_url+"\n") in previously_saved or \
            download_url.endswith("/"):
            continue

        print('Injecting retrieval code into web page')
        driver.execute_script("""
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
            downloaded_file = driver.execute_script('return (window.file_contents !== null ? window.file_contents.split(\',\')[1] : null);')
            #print(downloaded_file)
            if not downloaded_file:
                print('\tNot downloaded, waiting...')
                time.sleep(1.5)
        print('\tDone')

        save_file(download_url)

        save_downloaded(download_url)

        print('\tDone')

driver.close() # close web browser before exit