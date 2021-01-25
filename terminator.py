"""
Plugin for terminator

Copy this file to $HOME/.config/terminator/plugins/

Based on:
https://terminator-gtk3.readthedocs.io/en/latest/plugins.html
"""

import re
import terminatorlib.plugin as plugin

AVAILABLE = ['suse_bugzilla', 'suse_jira']


class base(plugin.URLHandler):
    capabilities = ['url_handler']

    def callback(self, line):
        for item in re.findall(self._extract, line):
            return self._url + item


class suse_bugzilla(base):
    handler_name = 'suse_bugzilla'
    match = r'\b((?:bsc|bnc)#[0-9]+)\b'
    nameopen = "Open Bugzilla bug"
    namecopy = "Copy Bugzilla URL"
    _extract = '[0-9]+'
    _url = 'https://bugzilla.suse.com/show_bug.cgi?id='


class suse_jira(base):
    handler_name = 'suse_jira'
    match = r'\b(jsc#[A-Z]+-[0-9]+)\b'
    nameopen = "Open Jira item"
    namecopy = "Copy Jira URL"
    _extract = '[A-Z]+-[0-9]+'
    _url = 'https://jira.suse.com/browse/'
