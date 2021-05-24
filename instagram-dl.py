import requests
import json
import http.cookiejar
import wget
import argparse
from pathlib import Path
import datetime

# Constants
DEFAULT_TEMPLATE = "./Instagram/{creator}/{creator}-{date}-{id}.{ext}"


# Functions
def check_status_code(status):
    if args.verbose:
        print("[VERBOSE] requests.get returned status code", status)
    if status == 200:
        # Specific success case
        print("[INFO] Access to the page was granted. Continuing.")
    elif 200 < status < 300:
        # Generic Success Case
        print("[INFO] Site returned success code:", status, ". Continuing.")
    elif status == 429:
        raise ConnectionRefusedError("[ERR] You need to log in or you need to follow that private account.")
    elif 400 <= status < 500:
        raise ConnectionRefusedError("[ERR] URL returned generic client error:", status)
    elif 500 <= status < 600:
        raise ConnectionRefusedError("[ERR] URL returned server error:", status)
    else:
        print("[WARN] requests.get returned unknown status code: ", status, " Continuing anyway.")


def download_json_manifest():
    try:
        # Try loading JSON without logging in
        check_status_code(requests.get(jsonURL).status_code)
        json_dict = json.loads(requests.get(jsonURL).content)
        print("[INFO] Access granted without login. Continuing.")
    except ConnectionRefusedError:
        # Import cookies to avoid the need to login and load JSON
        if args.cookieFile:
            print("[INFO] Login required. Loading cookie file.")
            cookies_file = http.cookiejar.MozillaCookieJar(args.cookieFile)
            cookies_file.load()
            check_status_code(requests.get(jsonURL, cookies=cookies_file).status_code)
            json_dict = json.loads(requests.get(jsonURL, cookies=cookies_file).content)
        else:
            raise
    return json_dict


def get_post_info():
    user = jsonDict['graphql']['shortcode_media']['owner']['username']
    date = datetime.datetime.fromtimestamp(jsonDict['graphql']['shortcode_media']
                                           ['taken_at_timestamp']).strftime('%Y-%m-%d')
    return user, date


def download_multiple_photos(unique_urls, unique_ids, unique_exts):
    try:
        # If -s was specified, skip this code
        if not args.single:
            children_url = jsonDict['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
            print("[INFO]: Multiple Photos Found: Downloading All.")
            no_of_children = len(children_url)
            # Cycle through children URLs
            for c in range(no_of_children):
                if children_url[c]['node']['display_url'] not in uniqueURLs:
                    child_url = children_url[c]['node']['display_resources']
                    unique_urls.append(child_url[len(child_url) - 1]['src'])
                    unique_ids.append(children_url[c]['node']['id'])
                    unique_exts.append(child_url[len(child_url) - 1]['src'].split('?', )[0].split('.')[-1])
    except KeyError:
        print("[INFO]: Only One Photo Found. Downloading.")
    return unique_urls, unique_ids, unique_exts


def construct_output():
    output_file = args.output_template.format(creator=username, date=timestamp, id=uniqueIDs[i], ext=uniqueExts[i])
    output_path = output_file.split('/')
    output_path = Path('/'.join(output_path[0:len(output_path) - 1]))

    # Check if base folder already exists, make it if not
    if not output_path.is_dir():
        output_path.mkdir(parents=True)

    return output_file, output_path


# Get Input Arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("URL", help="The URL from the instagram post you wish to download", type=str)
parser.add_argument("-c", "--cookies", dest="cookieFile", help="Path to cookies.txt file (Netscape cookie file format)",
                    type=str)
parser.add_argument("-s", "--single",
                    help="Download only the first photo that appears in the URL. Disabled by default.",
                    action="store_true")
parser.add_argument("-o", "--output-template", help="Output Template, in 'new Style' Python String Formatting",
                    default=DEFAULT_TEMPLATE)
parser.add_argument("-v", "--verbose", help="Print verbose messages", action="store_true")
args = parser.parse_args()

# Input validation
if args.cookieFile:
    if not Path(args.cookieFile).exists():
        raise FileNotFoundError("[ERR] The cookie file specified does not exist.")
if args.output_template == DEFAULT_TEMPLATE:
    print("[INFO] Outputting to script directory using default template:", DEFAULT_TEMPLATE)

# Target URL
jsonURL = args.URL + '?__a=1'  # Update the URL to get the JSON manifest
if args.verbose:
    print("[VERBOSE] JSON URL:", jsonURL)

# Download the JSON manifest
jsonDict = download_json_manifest()

# Extract post info
username, timestamp = get_post_info()

# Print verbose information
if args.verbose:
    print("[VERBOSE] Username: ", username)
    print("[VERBOSE] Date taken: ", timestamp)

# Extract picture URLs, IDs and Extensions
focusURL = jsonDict['graphql']['shortcode_media']['display_resources']
uniqueURLs = [focusURL[len(focusURL) - 1]['src']]  # The last entry in the JSON will be the highest resolution
uniqueIDs = [jsonDict['graphql']['shortcode_media']['id']]
uniqueExts = [uniqueURLs[0].split('?', )[0].split('.')[-1]]

# Check for multiple photos in the same post
uniqueURLs, uniqueIDs, uniqueExts = download_multiple_photos(uniqueURLs, uniqueIDs, uniqueExts)

# Download the pictures from the URLs
for i in range(len(uniqueURLs)):
    # Construct output file from template
    outputFile, outputPath = construct_output()

    if args.verbose:
        print("[VERBOSE] Filename:", outputFile)
        print("[VERBOSE] Downloading from:", uniqueURLs[i])
    if not Path(outputFile).exists():
        wget.download(uniqueURLs[i], out=outputFile)    # Only download if it doesn't already exist
    else:
        print(f"[WARN] {outputFile} already exists. Not downloading.")
