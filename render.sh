#!/bin/sh -e

# Download japan-latest.osm.pbf from https://download.geofabrik.de/asia/japan.html
# and follow https://hub.docker.com/r/overv/openstreetmap-tile-server

# docker volume create osm-data

# docker run \
#     -v $PWD/japan-latest.osm.pbf:/data.osm.pbf \
#     -v osm-data:/var/lib/postgresql/12/main \
#     overv/openstreetmap-tile-server \
#     import

# docker build -t osm-server .

docker run \
    -v $PWD/tiles:/tiles \
    -v osm-data:/var/lib/postgresql/12/main \
    -it osm-server
