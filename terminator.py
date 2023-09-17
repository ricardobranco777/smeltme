"""
Plugin for terminator

Copy this file to $HOME/.config/terminator/plugins/

Based on:
https://terminator-gtk3.readthedocs.io/en/latest/plugins.html
"""

import re
import terminatorlib.plugin as plugin

AVAILABLE = ['CVE', 'SUSE_Bugzilla', 'SUSE_Jira', 'SUSE_Incident', 'SUSE_Progress']


class Base(plugin.URLHandler):
    capabilities = ['url_handler']
    _extract = ""
    _url = ""

    def callback(self, url):
        for item in re.findall(self._extract, url):
            return f"{self._url}{item}"


class CVE(Base):
    handler_name = 'CVE'
    match = r'\bCVE-[0-9]+-[0-9]+\b'
    nameopen = "Open CVE item"
    namecopy = "Copy CVE URL"
    _extract = '[0-9]+-[0-9]+'
    _url = 'https://cve.mitre.org/cgi-bin/cvename.cgi?name='


class SUSE_Bugzilla(Base):
    handler_name = 'SUSE_Bugzilla'
    match = r'\b(bsc|bnc|boo)#[0-9]+\b'
    nameopen = "Open Bugzilla item"
    namecopy = "Copy Bugzilla URL"
    _extract = '[0-9]+'
    _url = 'https://bugzilla.suse.com/show_bug.cgi?id='


class SUSE_Jira(Base):
    handler_name = 'SUSE_Jira'
    match = r'\bjsc#[A-Z]+-[0-9]+\b'
    nameopen = "Open Jira item"
    namecopy = "Copy Jira URL"
    _extract = '[A-Z]+-[0-9]+'
    _url = 'https://jira.suse.com/browse/'


class SUSE_Incident(Base):
    handler_name = 'SUSE_Incident'
    match = r'\bS(USE)?:M(aintenance)?:[0-9]+:[0-9]+\b'
    nameopen = "Open Incident item"
    namecopy = "Copy Incident URL"
    _extract = '[0-9]+'
    _url = 'https://smelt.suse.de/incident/'


class SUSE_Progress(Base):
    handler_name = 'SUSE_Progress'
    match = r'\bpoo#[0-9]+\b'
    nameopen = "Open POO item"
    namecopy = "Copy POO URL"
    _extract = '[0-9]+'
    _url = 'https://progress.opensuse.org/issues/'
