"""Horizon d'un emplacement calculé à partir du LiDAR HD de l'IGN (données ouvertes, France).

Le MNS (modèle numérique de surface : sol, bâtiments, végétation) est parcouru en ligne droite depuis
l'instrument, dans chaque direction : la hauteur de l'horizon est l'angle le plus élevé rencontré.
La carte de classification indique si l'obstacle qui fixe l'horizon est de la végétation (en partie
transparente, surtout l'hiver) ou du bâti et du relief (opaques).
"""
import math
import struct
import urllib.parse
import urllib.request
import zlib
from datetime import date
from typing import Callable, List, Optional

WMS_URL = "https://data.geopf.fr/wms-r"
MNS_LAYER = "IGNF_LIDAR-HD_MNS_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93"
MNT_LAYER = "IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93"
CLASS_LAYER = "IGNF_LIDAR-HD_CLASS"
NO_DATA = -1000

# Grille fine autour de l'instrument (murs, arbres du jardin), grille large pour le lointain
NEAR_HALF_M, NEAR_RES_M = 150, 0.5
FAR_HALF_M, FAR_RES_M = 2000, 4.0
MAX_DISTANCE_M = 2000
# Couleur de la végétation dans la carte de classification de l'IGN (vert)
def is_vegetation(rgb) -> bool:
    r, g, b = rgb
    return g > 100 and g > r + 25 and g > b + 25


def lambert93(lat: float, lon: float):
    """Coordonnées GPS → Lambert-93 (EPSG:2154, ellipsoïde GRS80), projection native du LiDAR HD."""
    e, n, c = 0.0818191910428158, 0.7256077650532670, 11754255.426096
    xs, ys = 700000.0, 12655612.049876
    phi = math.radians(lat)
    iso = math.log(math.tan(math.pi / 4 + phi / 2) * ((1 - e * math.sin(phi)) / (1 + e * math.sin(phi))) ** (e / 2))
    r = c * math.exp(-n * iso)
    gamma = n * (math.radians(lon) - math.radians(3))
    return xs + r * math.sin(gamma), ys - r * math.cos(gamma)


def mercator(lat: float, lon: float):
    """Coordonnées GPS → Web Mercator (EPSG:3857), projection de la carte de classification."""
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) * 20037508.34 / math.pi
    return x, y


def _wms(fetch: Callable[[str, dict], bytes], layer: str, crs: str, bbox, size: int, fmt: str) -> bytes:
    return fetch(WMS_URL, {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": layer, "STYLES": "",
        "CRS": crs, "BBOX": ",".join(f"{v:.2f}" for v in bbox), "WIDTH": size, "HEIGHT": size, "FORMAT": fmt,
    })


class Grid:
    """Grille carrée centrée sur l'instrument, dont on lit une valeur par coordonnées relatives (m)."""

    def __init__(self, values, size: int, half: float):
        self.values, self.size, self.half = values, size, half
        self.res = 2 * half / size

    def at(self, dx: float, dy: float):
        col = int((dx + self.half) / self.res)
        row = int((self.half - dy) / self.res)
        if 0 <= col < self.size and 0 <= row < self.size:
            return self.values[row * self.size + col]
        return None


def _heights(fetch, x: float, y: float, layer: str, half: float, res: float) -> Grid:
    size = int(2 * half / res)
    data = _wms(fetch, layer, "EPSG:2154", (x - half, y - half, x + half, y + half), size, "image/x-bil;bits=32")
    if len(data) != size * size * 4:
        raise ValueError("Réponse inattendue du service LiDAR HD de l'IGN.")
    return Grid(struct.unpack(f"<{size * size}f", data), size, half)


def decode_png(data: bytes):
    """Décodeur PNG minimal (8 bits, RVB, RVBA ou palette) : la carte de classification n'existe qu'en image."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Image PNG attendue.")
    pos, idat, palette = 8, b"", None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", body[:10])
        elif kind == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    if depth != 8 or color not in (2, 3, 6):
        raise ValueError("Format PNG non pris en charge.")
    channels = {2: 3, 3: 1, 6: 4}[color]
    raw = zlib.decompress(idat)
    stride = width * channels
    pixels, previous = [], bytearray(stride)
    for row in range(height):
        start = row * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = previous[i]
            corner = previous[i - channels] if i >= channels else 0
            if kind == 1:
                line[i] = (line[i] + left) & 0xFF
            elif kind == 2:
                line[i] = (line[i] + up) & 0xFF
            elif kind == 3:
                line[i] = (line[i] + (left + up) // 2) & 0xFF
            elif kind == 4:
                p = left + up - corner
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - corner)
                line[i] = (line[i] + (left if pa <= pb and pa <= pc else up if pb <= pc else corner)) & 0xFF
        previous = line
        for col in range(width):
            if color == 3:
                pixels.append(palette[line[col]])
            else:
                pixels.append(tuple(line[col * channels:col * channels + 3]))
    return pixels, width


def _classes(fetch, lat: float, lon: float, half: float, res: float) -> Grid:
    # En Web Mercator, un mètre au sol vaut 1/cos(latitude) mètre de projection
    scale = 1 / math.cos(math.radians(lat))
    x, y = mercator(lat, lon)
    size = int(2 * half / res)
    data = _wms(fetch, CLASS_LAYER, "EPSG:3857", (x - half * scale, y - half * scale, x + half * scale, y + half * scale), size, "image/png")
    pixels, width = decode_png(data)
    return Grid(pixels, width, half)


def compute_horizon(lat: float, lon: float, instrument_height: float, fetch: Callable[[str, dict], bytes]) -> dict:
    """Profil d'horizon degré par degré : hauteur (°), obstacle végétal ou non, distance de l'obstacle (m)."""
    x, y = lambert93(lat, lon)
    near = _heights(fetch, x, y, MNS_LAYER, NEAR_HALF_M, NEAR_RES_M)
    far = _heights(fetch, x, y, MNS_LAYER, FAR_HALF_M, FAR_RES_M)
    ground_grid = _heights(fetch, x, y, MNT_LAYER, 2, 0.5)
    ground_values = sorted(v for v in ground_grid.values if v > NO_DATA)
    if not ground_values:
        raise ValueError("Pas de données LiDAR HD à cet endroit (zone non couverte ou interdite).")
    ground = ground_values[len(ground_values) // 2]
    # Le service refuse les images de plus de 512 pixels environ : 1 m suffit pour reconnaître un arbre
    classes = _classes(fetch, lat, lon, NEAR_HALF_M, 1.0)
    eye = ground + instrument_height

    def surface(dx, dy):
        for grid in (near, far):
            v = grid.at(dx, dy)
            if v is not None and v > NO_DATA:
                return v
        return None

    altitudes, vegetation, distances = [], [], []
    for degree in range(360):
        best, best_veg, best_d = 0.0, False, None
        # Deux rayons par degré : un obstacle étroit (poteau, tronc) n'échappe pas au calcul
        for az in (degree - 0.25, degree + 0.25):
            a = math.radians(az)
            sin_a, cos_a = math.sin(a), math.cos(a)
            d = 0.75
            while d < MAX_DISTANCE_M:
                v = surface(d * sin_a, d * cos_a)
                if v is not None:
                    angle = math.degrees(math.atan2(v - eye, d))
                    if angle > best:
                        rgb = classes.at(d * sin_a, d * cos_a)
                        best, best_veg, best_d = angle, bool(rgb and is_vegetation(rgb)), d
                d += 0.25 if d < 60 else 1.0 if d < 300 else 4.0
        altitudes.append(round(best, 1))
        vegetation.append(best_veg)
        distances.append(round(best_d, 1) if best_d else None)
    return {
        "alt": altitudes, "veg": vegetation, "distance": distances,
        "ground": round(ground, 2), "source": f"LiDAR HD IGN, calculé le {date.today():%d/%m/%Y}",
    }
