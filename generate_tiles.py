#!/usr/bin/env python3
import os
import threading
from math import atan, exp, log, pi, sin
from queue import Queue

import mapnik

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

# Default number of rendering threads to spawn, should be roughly equal to
# number of CPU cores available
NUM_THREADS = 4


def minmax(a, b, c):
    a = max(a, b)
    a = min(a, c)
    return a


class GoogleProjection:
    def __init__(self, levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        self.Ac = []
        c = 256
        for d in range(0, levels):
            e = c / 2
            self.Bc.append(c / 360.0)
            self.Cc.append(c / (2 * pi))
            self.zc.append((e, e))
            self.Ac.append(c)
            c *= 2

    def fromLLtoPixel(self, ll, zoom):
        d = self.zc[zoom]
        e = round(d[0] + ll[0] * self.Bc[zoom])
        f = minmax(sin(DEG_TO_RAD * ll[1]), -0.9999, 0.9999)
        g = round(d[1] + 0.5 * log((1 + f) / (1 - f)) * -self.Cc[zoom])
        return (e, g)

    def fromPixelToLL(self, px, zoom):
        e = self.zc[zoom]
        f = (px[0] - e[0]) / self.Bc[zoom]
        g = (px[1] - e[1]) / -self.Cc[zoom]
        h = RAD_TO_DEG * (2 * atan(exp(g)) - 0.5 * pi)
        return (f, h)


class RenderThread:
    def __init__(self, tile_dir, mapfile, q, printLock, maxZoom):
        self.tile_dir = tile_dir
        self.q = q
        self.m = mapnik.Map(256, 256)
        self.printLock = printLock
        # Load style XML
        # mapnik.load_map(self.m, mapfile, True)
        mapnik.load_map(self.m, mapfile)
        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj = GoogleProjection(maxZoom + 1)

    def render_tile(self, tile_uri, x, y, z):

        # Calculate pixel positions of bottom-left & top-right
        p0 = (x * 256, (y + 1) * 256)
        p1 = ((x + 1) * 256, y * 256)

        # Convert to LatLong (EPSG:4326)
        l0 = self.tileproj.fromPixelToLL(p0, z)
        l1 = self.tileproj.fromPixelToLL(p1, z)

        # Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0 = self.prj.forward(mapnik.Coord(l0[0], l0[1]))
        c1 = self.prj.forward(mapnik.Coord(l1[0], l1[1]))

        # Bounding box for the tile
        if hasattr(mapnik, "mapnik_version") and mapnik.mapnik_version() >= 800:
            bbox = mapnik.Box2d(c0.x, c0.y, c1.x, c1.y)
        else:
            bbox = mapnik.Envelope(c0.x, c0.y, c1.x, c1.y)
        render_size = 256
        self.m.resize(render_size, render_size)
        self.m.zoom_to_box(bbox)
        if self.m.buffer_size < 128:
            self.m.buffer_size = 128

        # Render image with default Agg renderer
        im = mapnik.Image(render_size, render_size)
        mapnik.render(self.m, im)
        im.save(tile_uri, "png256")

    def loop(self):
        while True:
            # Fetch a tile from the queue and render it
            r = self.q.get()
            if r is None:
                self.q.task_done()
                break
            else:
                (tile_uri, x, y, z) = r

            exists = ""
            if os.path.isfile(tile_uri):
                exists = "exists"
            else:
                self.render_tile(tile_uri, x, y, z)
            bytes = os.stat(tile_uri)[6]
            empty = ""
            if bytes == 103:
                empty = " Empty Tile "
            self.printLock.acquire()
            print(z, x, y, exists, empty)
            self.printLock.release()
            self.q.task_done()


def render_tiles(
    bbox, mapfile, tile_dir, minZoom=1, maxZoom=18, num_threads=NUM_THREADS
):
    print("render_tiles(", bbox, mapfile, tile_dir, minZoom, maxZoom, ")")

    # Launch rendering threads
    queue = Queue(32)
    printLock = threading.Lock()
    renderers = {}
    for i in range(num_threads):
        renderer = RenderThread(tile_dir, mapfile, queue, printLock, maxZoom)
        render_thread = threading.Thread(target=renderer.loop)
        render_thread.start()
        # print "Started render thread %s" % render_thread.getName()
        renderers[i] = render_thread

    # X,Y範囲を初期化
    minX = bbox[0]
    minY = bbox[1]
    maxX = bbox[2]
    maxY = bbox[3]

    for z in range(minZoom, maxZoom + 1):
        for x in range(minX, maxX + 1):
            path = f"{tile_dir}/{z}/{x}"
            os.makedirs(path, exist_ok=True)
            for y in range(minY, maxY + 1):
                tile_uri = f"{path}/{y}.png"
                t = (tile_uri, x, y, z)
                try:
                    queue.put(t)
                except KeyboardInterrupt:
                    raise SystemExit("Ctrl-c detected, exiting...")

        # ズームレベルを+1するのにあわせてX,Y範囲を更新
        minX = minX * 2
        maxX = maxX * 2 + 1
        minY = minY * 2
        maxY = maxY * 2 + 1

    # Signal render threads to exit by sending empty request to queue
    for i in range(num_threads):
        queue.put(None)
    # wait for pending rendering jobs to complete
    queue.join()
    for i in range(num_threads):
        renderers[i].join()


if __name__ == "__main__":
    mapfile = "/home/renderer/src/openstreetmap-carto/mapnik.xml"
    tile_dir = "/tiles"

    bbox = (452, 199, 453, 200)
    render_tiles(bbox, mapfile, tile_dir, 9, 15)
