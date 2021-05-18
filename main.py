import requests
import json
import http.cookiejar
import wget

# Output Path
outPath = "Instagram/"

# Target URL
instaURL = 'https://www.instagram.com/p/CHBGznoLvlEHd_ndv4YD0Qj9dGZtr67XLHk6vI0/?__a=1'

# Import cookies to avoid the need to login
cookiesFile = http.cookiejar.MozillaCookieJar("instagram.com_cookies.txt")
cookiesFile.load()

# Load the json file
jsonDict = json.loads(requests.get(instaURL, cookies=cookiesFile).content)

# Status 429 means login is required, 200 is successful login?
status = requests.get(instaURL, cookies=cookiesFile).status_code

# Extract picture URLs
focusURL = jsonDict['graphql']['shortcode_media']['display_resources']
focusURL = focusURL[len(focusURL)-1]['src']     # The last entry in the JSON will be the highest resolution
childrenURL = jsonDict['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
noOfChildren = len(childrenURL)
uniqueURLs = [focusURL]
# Cycle through children URLs (Not all posts have these, how do we handle this?)
for i in range(noOfChildren):
    if childrenURL[i]['node']['display_url'] not in uniqueURLs:
        uniqueURLs.append(childrenURL[i]['node']['display_url'])

# Download the pictures from the URLs
for i in range(len(uniqueURLs)):
    wget.download(uniqueURLs[i], out=outPath)

print("Status:", status)
print(uniqueURLs)
