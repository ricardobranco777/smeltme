FROM	python:3.8-alpine

RUN	apk add --no-cache tzdata && \

RUN	adduser -D user -h /user

COPY	smeltme /
RUN	python -OO -m compileall

ENV     PYTHONPATH /
ENV	PYTHONUNBUFFERED 1

WORKDIR	/user

USER	user
ENTRYPOINT ["/usr/local/bin/python3", "/smeltme"]
