#!/bin/sh -e

# https://hub.docker.com/r/overv/openstreetmap-tile-server

# docker volume create osm-data

# docker run \
#     -v $PWD/japan-latest.osm.pbf:/data.osm.pbf \
#     -v osm-data:/var/lib/postgresql/12/main \
#     overv/openstreetmap-tile-server \
#     import

docker run \
    -v $PWD/tiles:/tiles \
    -v osm-data:/var/lib/postgresql/12/main \
    -it osm-server
