# smeltme

Parse https://smelt.suse.de/overview/ for specified groups

[![Build Status](https://travis-ci.org/ricardobranco777/smeltme.svg?branch=master)](https://travis-ci.org/ricardobranco777/smeltme)

## Requirements

- Python 3
- python-dateutil (run `pip3 install --user python-dateutil` or install the `python3-python-dateutil` package in openSUSE or `python3-dateutil` in Debian/Ubuntu)

## Options

```
  -h, --help            show this help message and exit
  -a, --all             Show all. Ignore -g & -u options
  -c, --csv             CSV output
  -g GROUP, --group GROUP
                        Filter by group. May be specified multiple times
  -H, --no-header       Do not show header
  -j, --json            JSON output
  -k, --insecure        Allow insecure server connections when using SSL
  -u USER, --user USER
                        Filter by user. May be specified multiple times
  -s, --sort            Sort items by priority
  -r, --reverse         reverse sort
  -v, --verbose         Verbose. Show URL's for references
  -V, --version         Show version and exit
```

## Example

Open a tab for each Bugzilla entry:

```
for i in $(smeltme -u rbranco -v --csv -H | grep $package | awk -F, '{ print $9 }' | sed 's/|/ /g') ; do xdg-open $i ; done
```
