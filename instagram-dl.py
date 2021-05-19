import requests
import json
import http.cookiejar
import wget

# Output Path
outPath = "Instagram/"

# Target URL
instaURL = 'https://www.instagram.com/p/CPB9WEwh-G8/'
instaURL = instaURL + '?__a=1'  # Update the URL to get the JSON manifest

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

# Check for multiple photos in the same post
try:
    childrenURL = jsonDict['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
    print("[INFO]: Multiple Photos Found: Downloading All.")
    noOfChildren = len(childrenURL)
    uniqueURLs = [focusURL]
    # Cycle through children URLs (Not all posts have these, how do we handle this?)
    for i in range(noOfChildren):
        if childrenURL[i]['node']['display_url'] not in uniqueURLs:
            uniqueURLs.append(childrenURL[i]['node']['display_url'])
except KeyError:
    print("[INFO]: Only One Photo Found. Downloading.")
    uniqueURLs = [focusURL]

# Download the pictures from the URLs
for i in range(len(uniqueURLs)):
    wget.download(uniqueURLs[i], out=outPath)

print("Status:", status)
