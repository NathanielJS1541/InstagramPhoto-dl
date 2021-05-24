# InstagramPhoto-dl
The purpose of this python script is to offer a method to download photos from instagram with a URL similar to the way 
that `youtube-dl` works. This is intended to be installed in Termux on a phone with my custom 
[termux-url-opener](https://github.com/NathanielJS1541/Termux_youtube-dl_Configs.git) script to launch this script with 
the correct arguments.
#### *****A note of warning:** Using the login cookies from your instagram account and downloading large numbers of posts can get your account suspended as instagram flags this as "suspicious activity". I've been through two accounts so far testing this script.***
## Prerequisites
In order to run this script you need the following:
- [Python 3](https://www.python.org/downloads/) (I don't know whether older Python 3 versions will work, I tested with 
  Python 3.9.0). In order for this to work smoothly the Python install should be in your PATH (There is an option to
  check in the installer)
## Installation
### PC (Windows, Linux etc.)
Simply download the script from a browser, or `git clone https://github.com/NathanielJS1541/InstagramPhoto-dl.git` to a
suitable directory. Again, you should add this to PATH, so you don't have to type out the full path to the script every
time you run it. Alternatively you could just always run it from within the repo folder.

That's it, you can run the script with `python instagram-dl.py -h` for example.
### Termux
For Termux, you will need to either set up my
[configs for youtube-dl in Termux](https://github.com/NathanielJS1541/Termux_youtube-dl_Configs), or at least read
through the README to have the following set up and working:
- Termux and Termux API from the same appstore
- Fully upgraded the packages in Termux
- Given Termux access to the storage framework and installed the API properly
- Installed Python within Termux
- Created the ~/bin directory
- Write your own or use my 
  [termux-url-opener](https://github.com/NathanielJS1541/Termux_youtube-dl_Configs/blob/master/termux-url-opener.txt)
  bash script and have it saved in the ~/bin directory. If you use mine you may want to follow the whole guide to
  prevent errors.
- Allow Termux to draw over other apps (Share a URL to termux from any app, it should give you a pop-up explaining how
  to do this)
- Additionally, you may need to install git (`pkg install git`) if you want to directly clone the repo inside Termux

Once this is done, you can just clone the script into the ~/bin directory that you made with `cd ~/bin` and then `git 
clone https://github.com/NathanielJS1541/InstagramPhoto-dl.git`. Once this finishes, the termux-url-opener script should
be configured to launch this whenever it encounters an instagram URL.
## Usage
```
usage: instagram-dl.py [-h] [-c COOKIEFILE] [-s] [-o OUTPUT] [-v] URL

positional arguments:
  URL                   The URL from the instagram post you wish to download

optional arguments:
  -h, --help            show this help message and exit
  -c COOKIEFILE, --cookies COOKIEFILE
                        Path to cookies.txt file (Netscape cookie file format)
  -s, --single          Download only the first photo that appears in the URL. Disabled by default.
  -o OUTPUT, --output OUTPUT
                        Output Folder
  -v, --verbose         Print verbose messages

```
### Using Cookies
This script accepts a cookies.txt file (Netscape cookie file format) instead of using a username and password to log in
to download private content from accounts you follow. In order to do this, you will need to install the
[Cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
browser extension for Chromium browsers. This will allow you to log in to Instagram in chrome, and save the cookies to a
.txt file. This file can then be copied to whichever device the script will be run from and point the script to it with
the `-c` argument:
```bash
python ./instagram-dl.py -c ~/Documents/cookies.txt [URL]
```
The credentials in the cookies.txt file will expire, but you can always just save a new one and replace the old one.

## Not Working Yet / WIP
- Currently my termux-url-opener script can't distinguish between instagram photos and instagram videos. So either this
  script needs to learn to download videos too, or just pass the task on to youtube-dl.
- It's my exam season so I haven't really tested anything or spent much time on the readme, don't expect it to work 
  smoothly
- Need to add the ability to fall back to username/password authentication in the case a user doesn't want to use
  cookies, or the cookie is invalid.
- Should probably try to access the page regardless of whether cookies have been parsed first, if the page doesn't
  require authentication why bother providing it?