import socket

import requests
import json
import http.cookiejar
import wget
import argparse
from pathlib import Path
import datetime
import fileinput
import time

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


def download_json_manifest(json_url):
    try:
        # Try loading JSON without logging in
        raw_data = requests.get(json_url)
        check_status_code(raw_data.status_code)
        json_dict = json.loads(raw_data.content)
        print("[INFO] Access granted without login. Continuing.")
    except ConnectionRefusedError:
        # Import cookies to avoid the need to login and load JSON
        if args.cookieFile:
            print("[INFO] Login required. Loading cookie file.")
            cookies_file = http.cookiejar.MozillaCookieJar(args.cookieFile)
            cookies_file.load()
            raw_data = requests.get(json_url, cookies=cookies_file)
            check_status_code(raw_data.status_code)
            json_dict = json.loads(raw_data.content)
        else:
            raise
    return json_dict


def check_for_profile_url(url):
    test_json = url + "?__a=1"
    test_json = download_json_manifest(test_json)
    user = test_json['graphql']['user']['username']
    if "www.instagram.com/" + user in url:
        # This is a profile URL
        return True
    else:
        return False


def get_post_info(json_dict):
    user = json_dict['graphql']['shortcode_media']['owner']['username']
    date = datetime.datetime.fromtimestamp(json_dict['graphql']['shortcode_media']
                                           ['taken_at_timestamp']).strftime('%Y-%m-%d')
    return user, date


def get_profile_info(json_dict):
    user = json_dict['graphql']['user']['username']
    return user


def get_media_url(json_dict):
    if json_dict['__typename'] == 'GraphImage':
        # Post is a picture post
        focus_url = json_dict['display_resources']
        post_url = focus_url[len(focus_url) - 1]['src']  # The last entry in the JSON will be the highest resolution
    elif json_dict['__typename'] == 'GraphVideo':
        # Post is a video post
        post_url = json_dict['video_url']
    elif json_dict['__typename'] == 'GraphSidecar':
        if json_dict['is_video']:
            post_url = json_dict['edge_sidecar_to_children']['edges'][0]['node']['video_url']
        else:
            post_url = json_dict['edge_sidecar_to_children']['edges'][0]['node']['display_url']
    else:
        if args.verbose:
            print("[VERBOSE] JSON dictionary returned __typename:", json_dict['__typename'])
        raise ValueError("[ERR] Post media type was not understood.")
    return post_url


def get_multiple_post_urls(json_dict, unique_urls, unique_ids, unique_exts):
    try:
        # If -s was specified, skip this code
        if not args.single:
            children_url = json_dict['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
            print("[INFO]: Multiple Photos Found: Downloading All.")
            no_of_children = len(children_url)
            # Cycle through children URLs
            for c in range(no_of_children):
                media_url = get_media_url(children_url[c]['node'])
                if media_url not in unique_urls:
                    unique_urls.append(media_url)
                    unique_ids.append(children_url[c]['node']['id'])
                    unique_exts.append(media_url.split('?', )[0].split('.')[-1])
    except KeyError:
        print("[INFO] Only One Photo Found. Downloading.")
    return unique_urls, unique_ids, unique_exts


def construct_output(username, timestamp, unique_ids, unique_exts, url_no):
    output_file = args.output_template.format(creator=username, date=timestamp, id=unique_ids[url_no],
                                              ext=unique_exts[url_no])
    output_path = output_file.split('/')
    output_path = Path('/'.join(output_path[0:len(output_path) - 1]))

    # Check if base folder already exists, make it if not
    if not output_path.is_dir():
        output_path.mkdir(parents=True)

    return output_file


def download_post(post_url):
    # Download the JSON manifest
    json_dict = download_json_manifest(post_url)

    # Extract post info
    username, timestamp = get_post_info(json_dict)

    # Print verbose information
    if args.verbose:
        print("[VERBOSE] Username: ", username)
        print("[VERBOSE] Date taken: ", timestamp)

    # Extract post URLs, IDs and Extensions
    unique_urls = [get_media_url(json_dict['graphql']['shortcode_media'])]
    unique_ids = [json_dict['graphql']['shortcode_media']['id']]
    unique_exts = [unique_urls[0].split('?', )[0].split('.')[-1]]

    # Check for multiple media in the same post
    unique_urls, unique_ids, unique_exts = get_multiple_post_urls(json_dict, unique_urls, unique_ids, unique_exts)

    # Download the pictures from the URLs
    for i in range(len(unique_urls)):
        # Construct output file from template
        output_file = construct_output(username, timestamp, unique_ids, unique_exts, i)
        if args.verbose:
            print("\n[VERBOSE] Filename:", output_file)
            print("[VERBOSE] Downloading from:", unique_urls[i])
        if not Path(output_file).exists():
            retries = 0
            while retries <= 5:
                try:
                    wget.download(unique_urls[i], out=output_file)  # Only download if it doesn't already exist
                    retries = 5
                except socket.gaierror:
                    time.sleep(1)
                    retries += 1
                    print("[INFO] Socket Error. Retrying...")
            print()
        else:
            print(f"[WARN] {output_file} already exists. Not downloading.")
        if args.time:
            time.sleep(args.time)


def download_profile(profile_url):
    # Download the base JSON manifest
    json_dict = download_json_manifest(profile_url)

    # Extract profile info
    username = get_profile_info(json_dict)
    no_of_posts = json_dict['graphql']['user']['edge_owner_to_timeline_media']['count']
    cursor_pos = json_dict['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor'].replace(
        '=', '')
    user_id = json_dict['graphql']['user']['id']
    has_next_page = json_dict['graphql']['user']['edge_saved_media']['page_info']['has_next_page']
    # Print verbose information
    if args.verbose:
        print("[VERBOSE] Username: ", username)

    # Extract all profile photos
    # new_url = f"https://www.instagram.com/graphql/query/?query_hash=02e14f6a7812a876f7d133c9555b1151&variables=%7B" \
    #           f"%22id%22%3A%22{user_id}%22%2C%22first%22%3A{no_of_posts}%2C%22after%22%3A%22{cursor_pos}%3D%3D%22%7D"
    # if args.verbose:
    #     print("[VERBOSE] New URL: ", new_url)
    # json_dict = download_json_manifest(new_url)

    # Get full list of saved posts
    total_on_pages = 0
    while total_on_pages < no_of_posts:
        new_url = f"https://www.instagram.com/graphql/query/?query_hash=02e14f6a7812a876f7d133c9555b1151&variables=%7B" \
                  f"%22id%22%3A%22{user_id}%22%2C%22first%22%3A{no_of_posts}%2C%22after%22%3A%22{cursor_pos}%3D%3D%22%7D"
        if args.verbose:
            print("[VERBOSE] New URL: ", new_url)
        json_dict = download_json_manifest(new_url)

        media = json_dict['data']['user']['edge_owner_to_timeline_media']['edges']
        # Move to next cursor position
        for post in range(len(media)):
            shortcode = media[post]['node']['shortcode']
            # Download as a post
            url_sorter("https://www.instagram.com/p/" + shortcode + "/")
            if args.verbose:
                print("[VERBOSE] Post URL: " + "https://www.instagram.com/p/" + shortcode + "/")
        if has_next_page == "true":
            cursor_pos = json_dict['data']['user']['edge_saved_media']['page_info']['end_cursor'].replace('=', '')
            has_next_page = json_dict['data']['user']['edge_saved_media']['page_info']['has_next_page']
            if args.verbose:
                print("[VERBOSE] Cursor Position:", cursor_pos)


def download_saved(saved_url):
    # Download the base JSON manifest
    json_dict = download_json_manifest(saved_url)

    # Extract profile info
    no_of_saved = json_dict['graphql']['user']['edge_saved_media']['count']
    cursor_pos = json_dict['graphql']['user']['edge_saved_media']['page_info']['end_cursor'].replace('=', '')
    has_next_page = json_dict['graphql']['user']['edge_saved_media']['page_info']['has_next_page']
    user_id = json_dict['graphql']['user']['id']
    if args.verbose:
        print("[VERBOSE] Saved Photos:", no_of_saved)
        print("[VERBOSE] Cursor Position:", cursor_pos)

    # Get full list of saved posts
    total_on_pages = 0
    while total_on_pages < no_of_saved:
        new_url = f"https://www.instagram.com/graphql/query/?query_hash=2ce1d673055b99250e93b6f88f878fde&variables=%7B" \
                  f"%22id%22%3A%22{user_id}%22%2C%22first%22%3A{no_of_saved}%2C%22after%22%3A%22{cursor_pos}%3D%3D%22%7D"

        if args.verbose:
            print("[VERBOSE] New URL: ", new_url)
        json_dict = download_json_manifest(new_url)

        # Start cycling through media
        media = json_dict['data']['user']['edge_saved_media']['edges']
        total_on_pages += len(media)
        print(f"[INFO] Loaded {total_on_pages} out of {no_of_saved} posts")
        # Move to next cursor position
        for post in range(len(media)):
            shortcode = media[post]['node']['shortcode']
            # Download as a post
            url_sorter("https://www.instagram.com/p/" + shortcode + "/")
            if args.verbose:
                print("[VERBOSE] Post URL: " + "https://www.instagram.com/p/" + shortcode + "/")
        if has_next_page == "true":
            cursor_pos = json_dict['data']['user']['edge_saved_media']['page_info']['end_cursor'].replace('=', '')
            has_next_page = json_dict['data']['user']['edge_saved_media']['page_info']['has_next_page']
            if args.verbose:
                print("[VERBOSE] Cursor Position:", cursor_pos)


def url_sorter(url):
    if "www.instagram.com/p/" in url:
        # This is an instagram post
        post_json = url.replace("\n", "") + '?__a=1'  # Update the URL to get the JSON manifest
        download_post(post_json)
        if args.verbose:
            print("\n[VERBOSE] JSON URL:", post_json)
    elif "https://www.instagram.com/" in url and "/saved/" in url:
        # This is the user's saved photos
        saved_url = url.replace("\n", "") + '?__a=1'  # Update the URL to get the JSON manifest
        download_saved(saved_url)
        if args.verbose:
            print("\n[VERBOSE] JSON URL:", saved_url)
    elif check_for_profile_url(url):
        # URL is a profile
        profile_json = url.replace("\n", "") + '?__a=1'  # Update the URL to get the JSON manifest
        download_profile(profile_json)
        if args.verbose:
            print("\n[VERBOSE] JSON URL:", profile_json)
    else:
        # URL not implemented yet... panic!
        raise ValueError("[ERR] This type of URL has not been implemented yet!")


# Get Input Arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
inputURL = parser.add_mutually_exclusive_group(required=True)
inputURL.add_argument("URL", help="The URL from the instagram post or profile you wish to download", nargs='?',
                      type=str)
inputURL.add_argument("-b", "--batch-file", help="Path to a file containing multiple URLs to download from")
parser.add_argument("-c", "--cookies", dest="cookieFile", help="Path to cookies.txt file (Netscape cookie file format)",
                    type=str)
parser.add_argument("-t", "--time", help="The time that should be waited in seconds between photo downloads to try and"
                                         "appear less suspicious to instagram.", type=int)
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
if args.batch_file:
    if not Path(args.batch_file).exists():
        raise FileNotFoundError("[ERR] The batch file specified does not exist.")
if args.output_template == DEFAULT_TEMPLATE:
    print("[INFO] Outputting to script directory using default template:", DEFAULT_TEMPLATE)

# Target URL
if args.batch_file:
    for lines in fileinput.input(args.batch_file):
        url_sorter(lines)
else:
    url_sorter(args.URL)
