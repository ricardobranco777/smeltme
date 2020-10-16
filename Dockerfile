FROM	python:3.9-alpine

COPY	requirements.txt /tmp/

RUN	apk add --no-cache tzdata && \
	pip install --no-cache-dir -r /tmp/requirements.txt && \
	python -OO -m compileall

COPY	smeltme /

ENV     PYTHONPATH /
ENV	PYTHONUNBUFFERED 1

RUN	adduser -D user -h /user

WORKDIR	/user

USER	user
ENTRYPOINT ["/usr/local/bin/python3", "/smeltme"]
