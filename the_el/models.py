from django.contrib.gis.db import models
import locale


locale.setlocale(locale.LC_ALL, '')


class Stop(models.Model):
    """
    A stop for a bus or train. Multiple stops can exist in one station, but the stop is the
    meaningful entity here, the station itself an architectural entity only.
    """
    stop_id = models.IntegerField()
    name = models.CharField(max_length=200, null=True)
    desc = models.CharField(max_length=200, null=True)
    point = models.PointField(srid=4269, null=True)
    is_station = models.BooleanField(default=False)


class Route(models.Model):
    """
    A route taken by a vehicle, in general terms. I.E., Red line southbound.
    """
    route_id = models.CharField(max_length=25)
    short_name = models.CharField(max_length=150, null=True)
    long_name = models.CharField(max_length=300, null=True)
    desc = models.TextField(null=True)
    type = models.IntegerField(null=True)
    url = models.URLField(null=True)
    color = models.CharField(max_length=6, default='FFFFFF')
    text_color = models.CharField(max_length=6, default='000000')


class Shape(models.Model):
    """
    A shape for a particular route.
    """
    shape_id = models.IntegerField()
    line_string = models.LineStringField(null=True)

    def as_json(self):
        return self.line_string.geojson


class Trip(models.Model):
    """
    This is a scheduled instance of a route.
    """
    route = models.ForeignKey(Route, null=True)
    shape = models.ForeignKey(Shape, null=True)
    trip_id = models.BigIntegerField()
    run = models.CharField(max_length=20, null=True)
    direction = models.CharField(max_length=20, null=True)
