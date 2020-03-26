#!/usr/bin/env python

import functools
import itertools
import math
import operator
import string
import time

import geopy.distance
import requests

url = "https://randomstreetview.com/data"


def nToBase(n, base=64):
    sign = n < 0
    n = abs(n)
    if n == 0:
        return [0]

    digits = []
    while n:
        n, r = divmod(n, base)
        digits.append(r)

    return sign, digits[::-1]


def encodeBase(n, base=36):
    alphabet = string.digits + string.ascii_lowercase
    sign, digits = nToBase(int(n), base)
    digits = map(functools.partial(operator.getitem, alphabet), digits)
    return ("-" if sign else "") + "".join(digits)


def permalink(coord):
    a = encodeBase(float(coord["lat"]) * 1e6)
    b = encodeBase(float(coord["lng"]) * 1e6)
    # heading
    c = encodeBase(41, 36)
    # zoom
    d = encodeBase(10, 36)
    # pitch
    e = encodeBase(5, 36)
    return "https://randomstreetview.com/#{}".format("_".join([a, b, c, d, e]))


def query(country="all"):
    resp = requests.post(
        url,
        data={"country": country},
        headers={
            "Authority": "randomstreetview.com",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://randomstreetview.com",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Referer": "https://randomstreetview.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    resp.raise_for_status()
    data = resp.json()
    if data.get("success", False):
        return data["locations"]

    raise Exception(data)


def distance(a, b):
    a = (a["lat"], a["lng"])
    b = (b["lat"], b["lng"])
    d = geopy.distance.distance(a, b)
    return d.m


def main():
    home = {"lng": -92.019850, "lat": 30.213028}

    start = time.time()
    locations = []
    tries = 0
    while len(locations) < 10:
        tries += 1
        print("Try {}: fetching locations".format(tries))
        r = query()
        for location in r:
            location["dist"] = distance(home, location)
            location["href"] = permalink(location)
        r.sort(key=operator.itemgetter("dist"))
        r = itertools.takewhile(lambda x: x["dist"] < 100000, r)
        r = list(r)
        locations.extend(r)
        print(
            "Try {}: found {} locatings within 100km, have {}".format(
                tries, len(r), len(locations)
            )
        )

    dur = time.time() - start
    print("Took {:,.0f}s to find {} locations within 100km".format(dur, len(locations)))

    locations.sort(key=operator.itemgetter("dist"))
    for location in locations:
        print("{0[dist]: =10,.0f}m {0[formatted_address]} {0[href]}".format(location))


if __name__ == "__main__":
    main()
