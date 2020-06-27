# https://github.com/Overv/openstreetmap-tile-server
FROM overv/openstreetmap-tile-server

RUN apt-get install -y vim

COPY run.sh /
COPY generate_tiles.py /home/renderer/src
