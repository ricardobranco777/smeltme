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
  -c, --csv             CSV output (default: False)
  -r, --route {all,declined,ready,testing}
                        route to use (default: all)
  -v, --verbose         verbose. Show titles for URL's (default: False)
  --version             show program's version number and exit
```
