FROM node:16.13-alpine AS build-frontend

ADD . /app
WORKDIR /app/frontend
RUN yarn install && yarn generate

FROM python:3.8-buster
COPY --from=build-frontend /app /app
WORKDIR /app/backend
RUN pip install -U pip && \
    pip install -e '.[prod]' && \
    chmod 700 /app/docker_entrypoint.sh

ENTRYPOINT /app/docker_entrypoint.sh
