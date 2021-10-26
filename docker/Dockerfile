FROM python:3.9-alpine3.14

ENV FLASK_PORT 5042
ENV FLASK_APP api.app:create_app
ENV APP_PATH /app

RUN apk update \                                                                                                                                                          
    && apk --no-cache add git python3-dev build-base libffi-dev postgresql-libs postgresql-dev \
    && pip3 install wheel

COPY . /app
COPY ./docker/entrypoint.sh /entrypoint.sh

WORKDIR /app

RUN mkdir -p data/
RUN addgroup --gid 1000 apiuser
RUN adduser -u 1000 -D -G apiuser apiuser

RUN pip3 install -e . \
    && apk del git python3-dev build-base libffi-dev postgresql-dev

ENTRYPOINT ["/entrypoint.sh"]
HEALTHCHECK CMD curl --fail http://localhost:${FLASK_PORT}/health || exit 1