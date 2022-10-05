# selenium-bot-downloader
Python selenium-bot that downloads all files on an apache server and saves to a local folder.

Solution based on the interesting code suggested here: https://stackoverflow.com/a/36613546 <br />
Internal links of directory are scraped by adapting this solution https://stackoverflow.com/a/34631926

- Each time the download process happens, it can be via different IP adress
- Bot saves data on a local folder by mirroring the remote directory path. 
- Before downloading next time, the algorithm should check if a folder is already on my desktop. If not, it should download it
- Tested on sample target link of online directories: https://archive.ics.uci.edu/ml/machine-learning-databases/ipums-mld/
