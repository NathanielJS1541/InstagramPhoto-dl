import requests
import json
import http.cookiejar
import wget
import argparse
from pathlib import Path


# Functions
def check_status_code(status):
    if args.verbose:
        print("[VERBOSE] requests.get returned status code", status)
    if status == 429:
        raise ConnectionRefusedError("[ERR] The requested URL could not be accessed. Maybe you need to log in or "
                                     "don't have permission to view that page?")
    elif status == 200:
        print("[INFO] Access to the page was granted. Continuing.")
    else:
        print("[WARN] requests.get returned unknown status code. Continuing anyway.")


# Get Input Arguments
parser = argparse.ArgumentParser()
parser.add_argument("URL", help="The URL from the instagram post you wish to download", type=str)
parser.add_argument("-c", "--cookies", dest="cookieFile", help="Path to cookies.txt file (Netscape cookie file format)",
                    type=str)
parser.add_argument("-s", "--single",
                    help="Download only the first photo that appears in the URL. Disabled by default.",
                    action="store_true")
parser.add_argument("-o", "--output", help="Output Folder", default="./")
parser.add_argument("-v", "--verbose", help="Print verbose messages", action="store_true")
args = parser.parse_args()

# Test input arguments
if not Path(args.output).is_dir():
    raise FileNotFoundError("[ERR] The output folder specified does not exist.")
elif not Path(args.cookieFile).exists():
    raise FileNotFoundError("[ERR] The cookie file specified does not exist.")
elif args.output == "./":
    print("[INFO] Outputting to python script directory ./")

# Target URL
# jsonURL = 'https://www.instagram.com/p/CPB9WEwh-G8/'
jsonURL = args.URL + '?__a=1'  # Update the URL to get the JSON manifest
if args.verbose:
    print("[VERBOSE] JSON URL:", jsonURL)

# Import cookies to avoid the need to login and load JSON
if args.cookieFile:
    cookiesFile = http.cookiejar.MozillaCookieJar(args.cookieFile)
    cookiesFile.load()
    check_status_code(requests.get(jsonURL, cookies=cookiesFile).status_code)
    jsonDict = json.loads(requests.get(jsonURL, cookies=cookiesFile).content)
else:
    check_status_code(requests.get(jsonURL).status_code)
    jsonDict = json.loads(requests.get(jsonURL).content)

# Check access status

# Extract picture URLs
focusURL = jsonDict['graphql']['shortcode_media']['display_resources']
focusURL = focusURL[len(focusURL)-1]['src']     # The last entry in the JSON will be the highest resolution

# Check for multiple photos in the same post
try:
    uniqueURLs = [focusURL]
    # If -s was specified, skip this code
    if not args.single:
        childrenURL = jsonDict['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
        print("[INFO]: Multiple Photos Found: Downloading All.")
        noOfChildren = len(childrenURL)
        # Cycle through children URLs
        for i in range(noOfChildren):
            if childrenURL[i]['node']['display_url'] not in uniqueURLs:
                uniqueURLs.append(childrenURL[i]['node']['display_url'])
except KeyError:
    print("[INFO]: Only One Photo Found. Downloading.")
    uniqueURLs = [focusURL]

# Download the pictures from the URLs
for i in range(len(uniqueURLs)):
    if args.verbose:
        print("[VERBOSE] Downloading from:", uniqueURLs[i])
    wget.download(uniqueURLs[i], out=args.output)
