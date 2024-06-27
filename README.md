![Build Status](https://github.com/ricardobranco777/smeltme/actions/workflows/ci.yml/badge.svg)

# smeltme

Parse https://smelt.suse.de/overview/ using [API](https://tools.io.suse.de/smelt/user/api/index.html)

Docker image available at `ghcr.io/ricardobranco777/smeltme:latest`

## Requirements

- Python 3.11+
- python3-requests
- python3-requests-toolbelt (optional for debugging)

## Options

```
  -h, --help            show this help message and exit
  -a, --all             Show all. Ignore -g & -u options
  -c, --csv             CSV output
  -g GROUP, --group GROUP
                        Filter by group. May be specified multiple times
  -H, --no-header       Do not show header
  -j, --json            JSON output
  -u USER, --user USER
                        Filter by user. May be specified multiple times
  -s, --sort            Sort items by priority
  -r, --reverse         reverse sort
  -v, --verbose         Verbose. Show URL's for references
  --version             Show version and exit
```

## Example

Open a tab for each Bugzilla entry:

```
for i in $(smeltme -u rbranco -v --csv -H | grep $package | awk -F, '{ print $9 }' | sed 's/|/ /g') ; do xdg-open $i ; done
```
