FROM python:3.9-alpine3.14

ENV FLASK_PORT 5012
ENV FLASK_APP api.app:create_app
ENV APP_PATH /app

RUN apk update \                                                                                                                                                          
    && apk --no-cache add git python3-dev build-base \
    && pip3 install wheel

COPY . /app
COPY ./docker/entrypoint.sh /entrypoint.sh

WORKDIR /app

RUN pip3 install -e . \
    && apk del git python3-dev build-base

ENTRYPOINT ["/entrypoint.sh"]
HEALTHCHECK CMD curl --fail http://localhost:${FLASK_PORT}/health || exit 1