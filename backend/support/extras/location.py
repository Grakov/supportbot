import math


def deg2num(latitude, longitude, zoom):
    lat_rad = math.radians(latitude)
    n = 2.0 ** zoom
    x_tile = int((longitude + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x_tile, y_tile


def generate_tile_url(loc_x, loc_y, loc_zoom):
    return f'https://tile.openstreetmap.org/{loc_zoom}/{loc_x}/{loc_y}.png'


def generate_map_url(latitude, longitude, zoom, title=None, address=None):
    url = f'https://yandex.ru/maps/?ll={longitude}%2C{latitude}&z={zoom + 2}&mode=whatshere&whatshere[point]={longitude}' \
           f'%2C{latitude}&whatshere[zoom]={zoom + 2}'

    if title is not None:
        url += f'&text={title}'

    return url
