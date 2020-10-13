FROM	python:3.9-alpine

COPY	requirements.txt /tmp/

RUN	apk --no-cache --virtual .build-deps add \
		gcc \
		libc-dev \
		libffi-dev \
		make && \
	apk add --no-cache tzdata && \
	pip install --no-cache-dir -r /tmp/requirements.txt && \
	python -OO -m compileall && \
	ln -s /usr/local/bin/python3 /usr/bin/python3 && \
	apk del .build-deps

COPY	smeltme /

ENV     PYTHONPATH /
ENV	PYTHONUNBUFFERED 1

RUN	adduser -D user -h /user

WORKDIR	/user

USER	user
ENTRYPOINT ["/smeltme"]
