from bs4 import BeautifulSoup
from urllib.request import urlopen
import urllib.error
import urllib.robotparser
from socket import timeout
import time
from storage.storage import *

USER_AGENT = "user-agent=fri-wier-DOMACI_NJOKI"

def getResponseRobots(seed, db_connection):
    robots_url = 'http://' + seed + '/robots.txt'
    sitemap = response_robots = delay = None

    try:
        client = urlopen(robots_url, timeout=5)
        robots_page = client.read()
        client.close()
        soup = BeautifulSoup(robots_page, "html.parser")
        response_robots = str(soup)
    except Exception as e:
        print('Fetching robots.txt led to', e)

    if response_robots is not None:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        # CHECK IF ROBOTS ARE ALLOWED
        url = "http://" + seed
        if not rp.can_fetch(USER_AGENT, url):
            add_site(seed, response_robots, sitemap, delay, db_connection)
            print("Robots are not allowed on: ", seed)
            return "NOT ALLOWED", 0, 0
        delay = rp.crawl_delay(USER_AGENT)
        sitemap = rp.site_maps()

        # HANDLE REDIRECT
        if '<html>' in response_robots or '<!DOCTYPE html>' in response_robots:
            response_robots = None
    return response_robots, sitemap, delay


def getDisallowedFromRobotsFile(robots_file):
    disallowed = []
    robots_file = robots_file.split("\n")
    for line in robots_file:
        if "Disallow:" in line:
            split = line.split(" ")
            if len(split) > 1:
                disallowed.append(line.split(" ")[1])
    return disallowed


def getAllowedFromRobotsFile(robots_file):
    allowed = []
    robots_file = robots_file.split("\n")
    for line in robots_file:
        if "Allow:" in line:
            split = line.split(" ")
            if len(split) > 1:
                allowed.append(line.split(" ")[1])
    return allowed
