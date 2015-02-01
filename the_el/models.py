from django.contrib.gis.db import models
import locale


locale.setlocale(locale.LC_ALL, '')


class Stop(models.Model):
    """
    A stop for a bus or train. Multiple stops can exist in one station, but the stop is the
    meaningful entity here, the station itself an architectural entity only.
    """
    stop_id = models.IntegerField()
    stop_name = models.CharField(max_length=200, null=True)
    stop_desc = models.CharField(max_length=200, null=True)
    stop_point = models.PointField(srid=4269, null=True)
