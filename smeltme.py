#!/usr/bin/env python3
"""
Parse https://smelt.suse.de/overview/
"""

import argparse
import os
import sys
from itertools import zip_longest

import requests
from requests.exceptions import RequestException

try:
    from requests_toolbelt.utils import dump  # type: ignore
except ModuleNotFoundError:
    dump = None  # pylint: disable=invalid-name


VERSION = "2.0"

URL = "https://smelt.suse.de/api/v1/overview/testing/"
TIMEOUT = 15


session = requests.Session()


def debugme(got, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Print requests response
    """
    got.hook_called = True
    if dump is not None:
        print(dump.dump_all(got).decode("utf-8"), file=sys.stderr)
    return got


def get_info() -> list[dict]:
    """
    Get information
    """
    try:
        got = session.get(URL, timeout=TIMEOUT)
        got.raise_for_status()
    except RequestException as error:
        sys.exit(f"{URL}: {error}")
    data = got.json()
    results = data["results"]

    while data["next"]:
        try:
            got = session.get(data["next"], timeout=TIMEOUT)
            got.raise_for_status()
        except RequestException as error:
            sys.exit(f'{data["next"]}: {error}')
        data = got.json()
        results += data["results"]

    return results


def print_info(info: list, verbose: bool = False) -> None:
    """
    Print information
    """
    keys = ("ID", "PACKAGES", "CHANNELS", "REFERENCES")
    package_width = max(
        8, max(len(package) for item in info for package in item["packages"])
    )
    channel_width = max(
        8,
        max(
            len(version)
            for item in info
            for version in item["channellist"] + item["codestreams"]
        ),
    )
    fmt = f"{{:<16}}  {{:{package_width}}}  {{:{channel_width}}}  {{}}"
    print(fmt.format(*keys))
    for item in info:
        id_rr = f"{item['incident']['project'].replace('SUSE:Maintenance', 'S:M')}:{item['request_id']}"
        item["packages"] = item["packages"] or ["-"]
        item["packages"].sort()
        xkey = "channellist" if item["channellist"] else "codestreams"
        item[xkey] = item[xkey] or ["-"]
        item[xkey].sort()
        if verbose:
            refs = sorted(_["url"] for _ in item["incident"]["references"])
        else:
            # NOTE: Some entries have only "https:" in their name
            refs = sorted(
                _["name"]
                for _ in item["incident"]["references"]
                if _["name"] != "https:"
            )
        refs = refs or [""]
        print(fmt.format(id_rr, item["packages"][0], item[xkey][0], refs[0]))
        for package, channel, ref in zip_longest(
            item["packages"][1:],
            item[xkey][1:],
            refs[1:],
            fillvalue=" ",
        ):
            print(
                f"{' ': <16}  {package:{package_width}}  {channel:{channel_width}}  {ref}"
            )


def parse_opts():
    """
    Parse options and arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose. Show URL's for references",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> None:
    """
    Main function
    """
    opts = parse_opts()
    info = get_info()
    if not info:
        return
    print_info(info, verbose=opts.verbose)


if __name__ == "__main__":
    if os.getenv("DEBUG"):
        session.hooks["response"].append(debugme)
    try:
        main()
        session.close()
    except KeyboardInterrupt:
        sys.exit(1)
