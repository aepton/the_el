from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import date

from the_el.models import Route, Trip, Stop


def index(request):
    routes = Route.objects.all()
    return render(request, 'index.html', {
        'routes': routes
        })


def route_json(request, pkey):
    route = Route.objects.get(pk=pkey)
    trips = Trip.objects.filter(route=route)
    shapes = set()
    all_shapes = []
    trip_ids = set()
    for trip in trips:
        if trip.shape.shape_id not in shapes:
            shapes.add(trip.shape.shape_id)
            all_shapes.append(trip.shape.as_json())
    return JsonResponse({
        'shapes': all_shapes
    })

def route(request, pkey):
    route = Route.objects.get(pk=pkey)
    trips = Trip.objects.filter(route=route)
    shapes = set()
    all_shapes = []
    trip_ids = set()
    for trip in trips:
        if trip.shape.shape_id not in shapes:
            shapes.add(trip.shape.shape_id)
            all_shapes.append(trip.shape.as_json())
            #shape = list(trip.shape.line_string.coords)
            #shape.append(trip.shape.line_string.coords[0])
            #all_shapes.append(shape)
    return render(request, 'route.html', {
        'route': route,
        'trips': trips,
        'shapes': json.dumps(all_shapes),
        })
