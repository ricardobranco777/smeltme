"""
smeltme
"""

import argparse
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import zip_longest
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

try:
    from requests_toolbelt.utils import dump  # type: ignore
except ImportError:
    dump = None

BUGZILLA_TOKEN = os.getenv("BUGZILLA_TOKEN")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

MAX_ISSUES = 200
TIMEOUT = 15
VERSION = "1.9"

session = requests.Session()


@dataclass
class Issue:
    """
    Issue class
    """

    url: str
    title: str


def debugme(got, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Print requests response
    """
    got.hook_called = True
    if dump is not None:
        print(dump.dump_all(got).decode("utf-8"), file=sys.stderr)
    return got


def get_json(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    key: str | None = None,
) -> dict | list[dict] | None:
    """
    Get JSON
    """
    try:
        got = session.get(url, headers=headers, params=params, timeout=TIMEOUT)
        got.raise_for_status()
        data = got.json()
    except RequestException as error:
        print(f"ERROR: {url}: {error}", file=sys.stderr)
        return None
    if key is not None:
        return data[key]
    return data


def get_incidents(route: str = "testing") -> list[dict] | None:
    """
    Get incidents
    """
    url = f"https://smelt.suse.de/api/v1/overview/{route}/"
    data = get_json(url)
    if data is None:
        return None
    assert isinstance(data, dict)
    results = data["results"]
    while data["next"]:
        data = get_json(data["next"])
        if data is None:
            return None
        assert isinstance(data, dict)
        results.extend(data["results"])
    return results


def get_bugzilla_issues(host: str, urls: list[str]) -> list[Issue] | None:
    """
    Get Bugzilla issues
    """
    if not BUGZILLA_TOKEN and host in ("bugzilla.suse.com", "bugzilla.opensuse.org"):
        return None
    ids = [u.split("=")[-1] for u in urls]
    url = f"https://{host}/rest/bug"
    issues: list[Issue] = []
    for i in range(0, len(ids), MAX_ISSUES):
        params = {
            "id": ids[i : i + MAX_ISSUES],
            "include_fields": "id,summary",
        }
        if host in ("bugzilla.suse.com", "bugzilla.opensuse.org"):
            params["Bugzilla_api_key"] = str(BUGZILLA_TOKEN)
        try:
            got = session.get(url, params=params, timeout=TIMEOUT)
            got.raise_for_status()
        except RequestException as exc:
            # Prevent API key leaking in the URL
            error = str(exc).split("?", maxsplit=1)[0]
            print(f"ERROR: {url}: {error}", file=sys.stderr)
            return None
        issues.extend(
            [
                Issue(
                    url=f"https://{host}/show_bug.cgi?id={i['id']}", title=i["summary"]
                )
                for i in got.json()["bugs"]
            ]
        )
    return issues


def get_jira_issues(urls: list[str]) -> list[Issue] | None:
    """
    Get Jira issues
    """
    if not JIRA_TOKEN:
        return None
    ids = [os.path.basename(u) for u in urls]
    url = "https://jira.suse.com/rest/api/2/search"
    headers = {"Authorization": f"Bearer {JIRA_TOKEN}"}
    issues: list[Issue] = []
    for i in range(0, len(ids), MAX_ISSUES):
        params = {
            "fields": "summary",
            "jql": f"key in ({','.join(ids[i : i + MAX_ISSUES])})",
        }
        data = get_json(url, headers=headers, params=params, key="issues")
        if data is None:
            return None
        assert isinstance(data, list)
        issues.extend(
            [
                Issue(
                    url=f"https://jira.suse.com/browse/{i['key']}",
                    title=i["fields"]["summary"],
                )
                for i in data
            ]
        )
    return issues


def get_titles(urls: list[str]) -> dict[str, str]:
    """
    Get titles of issues
    """
    titles: dict[str, str] = {}

    # Handle multiple Bugzillas
    bugzillas: dict[str, list[str]] = defaultdict(list)
    for url in urls:
        urlx = urlparse(url)
        if urlx.netloc.startswith("bugzilla."):
            bugzillas[urlx.netloc].append(url)
    # Broken REST
    if "bugzilla.gnome.org" in bugzillas:
        del bugzillas["bugzilla.gnome.org"]
    for host in bugzillas:
        issues = get_bugzilla_issues(host, bugzillas[host])
        if issues is not None:
            titles |= {i.url: i.title for i in issues}

    # Handle Jira
    issues = get_jira_issues(
        list(filter(lambda u: u.startswith("https://jira.suse.com"), urls))
    )
    if issues is not None:
        titles |= {i.url: i.title for i in issues}
    return titles


def parse_opts():
    """
    Parse options and arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose. Show titles for URL",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def print_info(verbose: bool = False) -> None:
    """
    Print information
    """
    incidents = get_incidents()
    if incidents is None:
        return
    incidents.sort(key=lambda i: str.casefold(i["packages"][0]))
    # Filter CVE's since we track them on Bugzilla
    urls = [
        r["url"]
        for i in incidents
        for r in i["incident"]["references"] + i["references"]
        if not r["name"].startswith("CVE-")
    ]
    urls = list(set(urls))
    titles = {}
    if verbose:
        titles = get_titles(urls)
    package_width = max(8, max(len(p) for i in incidents for p in i["packages"]))
    fmt = f"{{:<20}}  {{:{package_width}}}  {{:12}}  {{}}"
    for incident in incidents:
        if not incident["packages"] or incident["packages"][0] == "update-test-trivial":
            continue
        request = ":".join(
            [
                incident["incident"]["project"].replace("SUSE:Maintenance", "S:M"),
                str(incident["request_id"]),
            ]
        )
        incident["packages"].sort()
        versions = list(sorted(v.split(":")[1] for v in incident["codestreams"]))
        bugrefs = [
            r["url"]
            for r in incident["incident"]["references"] + incident["references"]
            if not r["name"].startswith("CVE-")
        ]
        bugrefs = list(set(bugrefs)) or [""]
        bugrefs.sort()
        print(fmt.format(request, incident["packages"][0], versions[0], bugrefs[0]))
        for package, version, bugref in zip_longest(
            incident["packages"][1:],
            versions[1:],
            bugrefs[1:],
            fillvalue=" ",
        ):
            print(fmt.format("", package, version, bugref), end="")
            if verbose:
                print(" ", titles.get(bugref, ""))
            else:
                print()


def main() -> None:
    """
    Main function
    """
    opts = parse_opts()
    print_info(verbose=opts.verbose)


if __name__ == "__main__":
    if os.getenv("DEBUG"):
        session.hooks["response"].append(debugme)
    try:
        main()
        session.close()
    except KeyboardInterrupt:
        sys.exit(1)
