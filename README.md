![Build Status](https://github.com/ricardobranco777/smeltme/actions/workflows/ci.yml/badge.svg)

# smeltme

Parse https://smelt.suse.de/overview/ using [API](https://tools.io.suse.de/smelt/user/api/index.html)

Docker image available at `ghcr.io/ricardobranco777/smeltme:latest`

## Requirements

- Python 3.11+
- python3-requests
- python3-requests-toolbelt (optional for debugging)

## Tokens

To make the `-v` option work you need to have these variables setup in your environment:

- `BUGZILLA_TOKEN`
- `JIRA_TOKEN`

## Usage

`smeltme [-c] [-i] [-r {all,declined,ready,review,testing}] [-s] [-v] [-x] [package]`

## Options

```
  -h, --help            show this help message and exit
  -c, --csv             CSV output
  -i, --insensitive     case insensitive search
  -r, --route {all,declined,ready,review,testing}
                        May be specified multiple times. Default: all
  -s, --submission      Show submissions instead of requests
  -v, --verbose         verbose. Show titles for URL's
  -x, --regex           search regular expression
  --version             show program's version number and exit
```
