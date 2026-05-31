# Website

[![CI build](https://github.com/tjh90/website/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/tjh90/website/actions/workflows/build.yml)

Simple website

## Prerequisites

- Java 25
- Maven
- Docker & Docker Compose

## Building

Run the following commands from the repository root:

``` shell
# Compile web server code.
mvn clean install -P prod

# Build docker images.
sudo docker-compose --file ./build/compose.yml build
```

## Deploying with Docker

1. Copy your SSL certificate and key file to `./build/certs`
2. Run the following command:

```shell
sudo docker-compose --file ./build/compose.yml up
```
