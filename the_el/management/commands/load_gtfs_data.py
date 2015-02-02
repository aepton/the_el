import logging
import os

from csv import DictReader
from datetime import datetime
from django.conf import settings
from django.contrib.gis.geos import *
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand, CommandError

from the_el.models import Route, Shape, Stop, Trip


def load_stops():
    """
    Loads stops from GTFS-spec-compliant stops.txt file in data dir.
    """
    with open(os.path.join(settings.DATA_DIR, 'stops.txt')) as stopfile:
        reader = DictReader(stopfile)
        for line in reader:
            stop, created = Stop.objects.get_or_create(stop_id=int(line['stop_id']))
            stop.name = line['stop_name']
            stop.desc = line['stop_desc']
            stop.point = 'POINT(%s %s)' % (line['stop_lon'], line['stop_lat'])
            stop.is_station = True if line['location_type'] == 1 else False
            stop.save()


def load_routes():
    """
    Loads routes from GTFS-spec-compliant routes.txt file in data dir.
    """
    with open(os.path.join(settings.DATA_DIR, 'routes.txt')) as routefile:
        reader = DictReader(routefile)
        for line in reader:
            route, created = Route.objects.get_or_create(route_id=line['route_id'])
            route.short_name = line['route_short_name']
            route.long_name = line['route_long_name']
            route.type = line['route_type']
            route.url = line['route_url']
            route.color = line['route_color']
            route.text_color = line['route_text_color']
            route.save()


def load_shapes():
    """
    Loads shapes from GTFS-spec-compliant shapes.txt file in data dir.
    """
    Shape.objects.all().delete()
    with open(os.path.join(settings.DATA_DIR, 'shapes.txt')) as shapefile:
        reader = DictReader(shapefile)
        coords = []
        last_id = None
        for line in reader:
            shape, created = Shape.objects.get_or_create(shape_id=int(line['shape_id']))
            point = Point(float(line['shape_pt_lon']), float(line['shape_pt_lat']))
            if created:
                print 'On %s' % line['shape_id']
                if last_id is not None:
                    old_shape = Shape.objects.get(shape_id=last_id)
                    old_shape.line_string = LineString(coords)
                    old_shape.save()
                    coords = []
                coords.append(point)
            else:
                coords.append(point)
            last_id = line['shape_id']
            shape.save()
        if last_id is not None:
            old_shape = Shape.objects.get(shape_id=last_id)
            old_shape.line_string = LineString(coords)
            old_shape.save()


def load_trips():
    """
    Loads trips from GTFS-spec-compliant trips.txt file in data dir.
    """
    pass



class Command(BaseCommand):
    def handle(self, *args, **options):
        #load_stops()
        #load_routes()
        #load_shapes()
        load_trips()
        welles = Point(-87.686242, 41.962255)
        distance = 200
        points = Stop.objects.filter(point__distance_lte=(welles, D(m=distance)))
        for point in points:
            print point.desc
