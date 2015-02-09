import boto
import json
import logging
import os
import requests
import sys
import time
import xmltodict

from boto.s3.key import Key
from csv import DictReader
from datetime import datetime
from django.conf import settings
from django.contrib.gis.geos import *
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand, CommandError

from the_el.models import Route, Shape, Stop, Trip
from the_el.utils import get_key


def get_train_metadata():
    return {
        'red': {
            'color': '#C60C30',
            'name': 'Red Line'
        },
        'blue': {
            'color': '#00A1DE',
            'name': 'Blue Line'
        },
        'brn': {
            'color': '#62361B',
            'name': 'Brown Line'
        },
        'g': {
            'color': '#009B3A',
            'name': 'Green Line'
        },
        'org': {
            'color': '#F9461C',
            'name': 'Orange Line'
        },
        'p': {
            'color': '#522398',
            'name': 'Purple Line'
        },
        'pink': {
            'color': '#E27EA6',
            'name': 'Pink Line'
        },
        'y': {
            'color': '#F9E300',
            'name': 'Yellow Line'
        }
    }


def get_train_positions():
    """
    Gets all current train positions from CTA API
    """
    metadata = get_train_metadata()
    cta_url = ('http://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=%s&rt='
               'red,blue,brn,g,org,p,pink,y' % get_key(settings.CTA_TRAIN_KEY_FILE))
    logging.info('Fetching trains')
    try:
        response = xmltodict.parse(requests.get(cta_url, timeout=settings.TIMEOUT_LENGTH).text)
    except Exception:
        logging.warning('Timed out waiting for response from %s' % cta_url)
        return []
    trains = []
    for route in response['ctatt']['route']:
        for train in route.get('train', []):
            try:
                if train.get('lat', '') and train.get('lon', ''):
                    trains.append({
                        'route': metadata[route['@name']]['name'],
                        'run': train['rn'],
                        'type': 'train',
                        'dest': train['destNm'],
                        'lat': train['lat'],
                        'lon': train['lon'],
                        'color': metadata[route['@name']]['color'],
                        'heading': train['heading'],
                        'next': train['nextStaNm'],
                        'approaching': True if train['isApp'] else False,
                        'delayed': True if train['isDly'] else False
                        })
            except Exception:
                pass
    return trains


def get_bus_positions_for_selected_routes(routes):
    """
    Given a list of up to 10 routes, fetches and returns all bus positions from CTA API
    """
    logging.info('Fetching these routes: %s' % ', '.join(routes))
    vehicles_url = ('http://www.ctabustracker.com/bustime/api/v1/getvehicles?key=%s&rt=%s' %
                    (get_key(settings.CTA_BUS_KEY_FILE), ','.join(routes[:10])))
    try:
        response = xmltodict.parse(requests.get(vehicles_url).text, timeout=settings.TIMEOUT_LENGTH)
    except Exception:
        logging.warning('Timed out waiting for response from %s' % vehicles_url)
        return None
    return response


def get_bus_positions():
    """
    Gets all current bus positions
    """
    routes_url = ('http://www.ctabustracker.com/bustime/api/v1/getroutes?key=%s'
                  % get_key(settings.CTA_BUS_KEY_FILE))
    logging.info('Fetching all routes')
    try:
        response = xmltodict.parse(requests.get(routes_url).text, timeout=settings.TIMEOUT_LENGTH)
    except Exception:
        logging.warning('Timed out waiting for response from %s' % routes_url)
        return []
    routes = []
    all_buses = []
    buses_json = []
    route_meta = {}
    for route in response['bustime-response']['route']:
        if len(routes) == 10:
            buses = get_bus_positions_for_selected_routes(routes)
            for vehicle in buses.get('bustime-response', {}).get('vehicle', []):
                all_buses.append(vehicle)
            routes = []
        routes.append(route['rt'])
        route_meta[route['rt']] = {'name': route['rtnm'], 'color': route['rtclr']}
    buses = get_bus_positions_for_selected_routes(routes)
    for vehicle in buses.get('bustime-response', {}).get('vehicle', []):
        all_buses.append(vehicle)
    for bus in all_buses:
        try:
            buses_json.append({
                'route': '%s %s' % (bus['rt'], route_meta[bus['rt']]['name']),
                'run': bus['vid'],
                'type': 'bus',
                'dest': bus['des'],
                'lat': bus['lat'],
                'lon': bus['lon'],
                'color': route_meta[bus['rt']]['color'],
                'heading': bus['hdg'],
                'delayed': True if bus.get('dly', False) else False,
                'speed': None if not bus.get('spd', False) else bus['spd']
                })
        except Exception, e:
            print e
    return buses_json


def upload_data_to_s3(s3_bucket, filename, directory_path, data_str):
    """
    Uploads the data_str as a file named filename to directory_path (not ending in /) in s3_bucket.
    """
    s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = s3.get_bucket(s3_bucket)
    key = Key(bucket)
    key.key = '%s/%s' % (directory_path, filename)
    key.set_contents_from_string(data_str)
    key.make_public()


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Check PID file, quit if we're still running. Not super robust but who cares.
        pid = str(os.getpid())
        pidfile = '/tmp/load_positions.pid'
        if os.path.isfile(pidfile):
            logging.error('%s already exists, exiting' % pidfile)
            sys.exit()
        else:
            file(pidfile, 'w').write(pid)

        runs = 0
        while runs < 3:
            trains = get_train_positions()
            buses = get_bus_positions()
            #"""
            if trains:
                upload_data_to_s3(
                    settings.EL_S3_BUCKET, 'train_positions.json', 'static', json.dumps(trains))
            if buses:
                upload_data_to_s3(
                    settings.EL_S3_BUCKET, 'bus_positions.json', 'static', json.dumps(buses))
            if trains or buses:
                upload_data_to_s3(
                    settings.EL_S3_BUCKET, 'all_positions.json', 'static', json.dumps(
                        trains + buses))
            """
            with open(os.path.join(settings.EL_STATIC_DIR, 'train_positions.json'), 'w') as posfile:
                posfile.write(json.dumps(trains))
                posfile.close()
            with open(os.path.join(settings.EL_STATIC_DIR, 'bus_positions.json'), 'w') as posfile:
                posfile.write(json.dumps(buses))
                posfile.close()
            with open(os.path.join(settings.EL_STATIC_DIR, 'all_positions.json'), 'w') as posfile:
                posfile.write(json.dumps(trains + buses))
                posfile.close()
            """
            runs += 1
            if runs < 3:
                # Sleep and run 3 times, leave headroom for all runs to complete in under a minute
                time.sleep(12)

        os.unlink(pidfile)
