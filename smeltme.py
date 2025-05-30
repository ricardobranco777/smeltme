#!/usr/bin/env python3
"""
Parse https://smelt.suse.de/overview/
"""

import argparse
import os
import sys
from datetime import datetime, timezone
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


def print_info(  # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
    info: list,
    no_header: bool = False,
    csv: bool = False,
    sort: bool = False,
    reverse: bool = False,
    verbose: bool = False,
) -> None:
    """
    Print information
    """
    keys = (
        "ID",
        "RATING",
        "CREATED",
        "DUE",
        "PRIO",
        "PACKAGES",
        "CHANNELS",
        "REFERENCES",
    )
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
    fmt = f"{{:<16}}  {{:<10}} {{:<11}} {{:<6}}  {{:<5}}  {{:{package_width}}}  {{:{channel_width}}}  {{}}"
    if not no_header:
        print(",".join(keys) if csv else fmt.format(*keys))
    if sort:
        info.sort(key=lambda item: item["incident"]["priority"], reverse=reverse)
    for item in info:
        id_rr = f"{item['incident']['project'].replace('SUSE:Maintenance', 'S:M')}:{item['request_id']}"
        rating = item["incident"]["rating"]["name"]
        created = item["created"][: len("YYYY-MM-DD")]
        due = "-"
        if item["incident"]["deadline"] is not None:
            enddate = datetime.fromisoformat(item["incident"]["deadline"][:-1]).replace(
                tzinfo=timezone.utc
            ) - datetime.now(timezone.utc)
            if enddate is not None:
                due = f"{enddate.days}d"
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
        if csv:
            print(
                id_rr,
                rating,
                created,
                due,
                str(item["incident"]["priority"]),
                "|".join(item["packages"]),
                "|".join(item[xkey]),
                "|".join(refs),
                sep=",",
            )
        else:
            print(
                fmt.format(
                    id_rr,
                    rating,
                    created,
                    due,
                    item["incident"]["priority"],
                    item["packages"][0],
                    item[xkey][0],
                    refs[0],
                )
            )
            for package, channel, ref in zip_longest(
                item["packages"][1:],
                item[xkey][1:],
                refs[1:],
                fillvalue=" ",
            ):
                print(
                    f"{' ': <54}  {package:{package_width}}  {channel:{channel_width}}  {ref}"
                )


def parse_opts():
    """
    Parse options and arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--csv", action="store_true", help="CSV output")
    parser.add_argument(
        "-H", "--no-header", action="store_true", help="Do not show header"
    )
    parser.add_argument(
        "-s", "--sort", action="store_true", help="Sort items by priority"
    )
    parser.add_argument("-r", "--reverse", action="store_false", help="reverse sort")
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
    if info:
        print_info(
            info,
            no_header=opts.no_header,
            csv=opts.csv,
            sort=opts.sort,
            reverse=opts.reverse,
            verbose=opts.verbose,
        )


if __name__ == "__main__":
    if os.getenv("DEBUG"):
        session.hooks["response"].append(debugme)
    try:
        main()
        session.close()
    except KeyboardInterrupt:
        sys.exit(1)
