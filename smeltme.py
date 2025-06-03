#!/usr/bin/env python3
"""
smeltme
"""

import argparse
import re
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import chain, zip_longest
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
VERSION = "2.1"

ANSI_RESET = "\033[0m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"

PRODUCTS = re.compile(
    r"(SLE|SUSE-MicroOS)-(?:INSTALLER|Module|Product|HA|SAP|SERVER).*?_(1[25](?:-SP\d)).*"
)

is_tty = sys.stdout.isatty()
session = requests.Session()


@dataclass(frozen=True)
class Reference:
    """
    Reference class
    """

    url: str
    title: str

    def __str__(self) -> str:
        if not self.url:
            return ""
        # name sucks so we rebuild it here
        tag = "".join([s[0] for s in str(urlparse(self.url).hostname).split(".")])
        issue = (
            self.url.split("=")[-1] if "=" in self.url else os.path.basename(self.url)
        )
        tag = f"{tag}#{issue}"
        if self.title:
            return f"{tag:<13}  {self.title}"
        return tag


@dataclass(frozen=True)
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


def get_incidents(route: str) -> list[dict]:
    """
    Get incidents
    """
    results: list[dict] = []
    url = f"https://smelt.suse.de/api/v1/overview/{route}/"
    data = get_json(url)
    if data is None:
        return results
    assert isinstance(data, dict)
    results.extend(data["results"])
    while data["next"]:
        data = get_json(data["next"])
        if data is None:
            return results
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
                    url=f"https://{host}/show_bug.cgi?id={i['id']}",
                    title=i["summary"],
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


def get_titles(urls: set[str]) -> dict[str, str]:
    """
    Get titles of issues
    """
    titles: dict[str, str] = {}
    bugzillas: dict[str, list[str]] = defaultdict(list)
    jira_urls: list[str] = []

    for url in urls:
        urlx = urlparse(url)
        if urlx.netloc.startswith("bugzilla."):
            bugzillas[urlx.netloc].append(url)
        elif urlx.netloc.startswith("jira."):
            jira_urls.append(url)

    # Remove unsupported Bugzillas
    bugzillas.pop("bugzilla.gnome.org", None)

    with ThreadPoolExecutor() as executor:
        futures = []
        for host, bug_urls in bugzillas.items():
            futures.append(executor.submit(get_bugzilla_issues, host, bug_urls))
        if jira_urls:
            futures.append(executor.submit(get_jira_issues, jira_urls))
        for future in as_completed(futures):
            issues = future.result()
            if issues is not None:
                titles |= {i.url: i.title for i in issues}

    return titles


def parse_opts():
    """
    Parse options and arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--csv", action="store_true", help="CSV output")
    parser.add_argument(
        "-r",
        "--route",
        action="append",
        choices=[
            "all",
            "declined",
            "ready",
            "review",
            "testing",
        ],
        help="May be specified multiple times. Default: all",
    )
    parser.add_argument(
        "-s",
        "--submission",
        action="store_true",
        help="Show submissions instead of requests",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose. Show titles for URL's",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def get_all_incidents(routes: list[str]) -> list[dict]:
    """
    Get all incidents
    """
    with ThreadPoolExecutor(max_workers=len(routes)) as executor:
        results = executor.map(get_incidents, routes)
    incidents = list(chain.from_iterable(results))
    if incidents:
        incidents.sort(key=lambda i: str.casefold(i["packages"][0]))
    return incidents


def get_versions(channels: list[str], codestreams: list[str]) -> list[str]:
    """
    Get product versions from list of channels & codestreams
    """
    versions: list[str] = list(sorted(c.split(":")[1] for c in codestreams))
    curated = {
        PRODUCTS.sub(r"\1-\2", channel)
        for channel in channels
        if "SP" in channel or "Micro" in channel
    }
    # Use SLE-Micro for everything
    curated = {m.replace("SUSE-MicroOS", "SLE-Micro") for m in curated}
    return list(sorted(set(versions) | curated))


def get_references(incident: dict) -> list[dict]:
    """
    Get references for incident or submission
    """
    if incident["incident"]:
        return incident["incident"]["references"]
    return incident["references"]


def print_info(  # pylint: disable=too-many-locals
    routes: list[str], csv: bool = False, verbose: bool = False
) -> None:
    """
    Print requests
    """
    incidents = get_all_incidents(routes)
    if not incidents:
        return
    # Filter CVE's since we track them on Bugzilla
    titles = {}
    if verbose and not csv:
        titles = get_titles(
            {
                r["url"]
                for i in incidents
                for r in get_references(i)
                if not r["name"].startswith("CVE-")
            }
        )
    package_width = max(8, max(len(p) for i in incidents for p in i["packages"] if p))
    fmt = "{:16}" if incidents[0]["incident"] else "{:6}"
    fmt += f"  {{:{package_width}}}  {{:16}} {{}}"
    print(fmt)
    for incident in incidents:
        packages: list[str] = list(sorted(filter(None, incident["packages"])))
        if not packages or packages[0] == "update-test-trivial":
            continue
        request = str(incident["request_id"])
        status = incident["status"]["name"]
        versions = get_versions(incident["channellist"], incident["codestreams"])
        if incident["incident"]:
            incident = incident["incident"]
        if "project" in incident:
            request = (
                incident["project"].replace("SUSE:Maintenance", "S:M") + ":" + request
            )
        if is_tty and len(routes) > 1:
            if status == "ready":
                request = f"{ANSI_GREEN}{request}{ANSI_RESET}"
            elif status == "declined":
                request = f"{ANSI_RED}{request}{ANSI_RESET}"
        bugrefs: list[Reference] = [
            Reference(url=r["url"], title=titles.get(r["url"], ""))
            for r in sorted(incident["references"], key=lambda i: i["url"])
            if not r["name"].startswith("CVE-")
        ]
        bugrefs = bugrefs or [Reference(url="", title="")]
        if csv:
            print(
                request,
                " ".join(packages),
                " ".join(versions),
                " ".join(str(b) for b in bugrefs),
                sep=",",
            )
        else:
            print(fmt.format(request, packages[0], versions[0], bugrefs[0]))
            for package, version, bugref in zip_longest(
                packages[1:],
                versions[1:],
                bugrefs[1:],
                fillvalue=" ",
            ):
                print(fmt.format("", package, version, bugref))


def main() -> None:
    """
    Main function
    """
    opts = parse_opts()
    opts.route = opts.route or ["all"]
    routes = []
    for route in opts.route:
        if route == "all":
            if opts.submission:
                routes = ["submission_ready", "submission_review"]
            else:
                routes = ["tested_declined", "tested_ready", "testing"]
            break
        if opts.submission:
            if route in {"ready", "review"}:
                route = f"submission_{route}"
        else:
            if route in {"declined", "ready"}:
                route = f"tested_{route}"
        routes.append(route)
    routes = list(set(routes))
    print_info(routes, csv=opts.csv, verbose=opts.verbose)


if __name__ == "__main__":
    if os.getenv("DEBUG"):
        session.hooks["response"].append(debugme)
    try:
        main()
        session.close()
    except KeyboardInterrupt:
        sys.exit(1)
