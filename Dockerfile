FROM	registry.opensuse.org/opensuse/bci/python:latest

RUN	zypper addrepo https://download.opensuse.org/repositories/SUSE:/CA/openSUSE_Tumbleweed/SUSE:CA.repo && \
	zypper --gpg-auto-import-keys -n install ca-certificates-suse && \
	zypper -n install python3-requests \
		python3-requests-toolbelt && \
	zypper clean -a

COPY	smeltme /smeltme

VOLUME	/root

ENTRYPOINT ["/usr/bin/python3", "/smeltme"]
