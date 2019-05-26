#! python3
# Wikipedia crawler
import json
import os
import re
import urllib.request

WIKI_URL = "https://en.wikipedia.org/wiki/"
START = "London"
LINK_PATTERN = re.compile(br'href="/wiki/(\w+)"')
BANNED_LINKS = {"Main_Page"}
MAX_LEVEL = 1

try:
    with open("wiki.json", "r") as f:
        visited = json.load(f)
except FileNotFoundError:
    visited = {}


def download(name):
    if name in visited:
        with open("wiki/%s" % name, "rb") as f:
            webData = f.read()
    else:
        r = urllib.request.urlopen(WIKI_URL + name)
        webData = r.read()
        with open("wiki/%s" % name, "wb") as f:
            f.write(webData)
    return webData


def tree(name, level=0):
    if name in visited:
        return
    webData = download(name)
    print("+" + "-" * level, name, len(webData))
    if level == MAX_LEVEL:
        return

    _links = set(i.decode() for i in LINK_PATTERN.findall(webData))
    links = sorted(_links - BANNED_LINKS)
    for i in links:
        tree(i, level=level + 1)
    visited[name] = links

    try:
        with open("wiki.json", "w") as f:
            json.dump(visited, f)
    except KeyboardInterrupt:
        with open("wiki.json", "w") as f:
            json.dump(visited, f)
        raise KeyboardInterrupt


if __name__ == "__main__":
    tree(START)
