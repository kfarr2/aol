import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from aol.lakes.models import NHDLake
from aol.facilities.models import Facility
from aol.lakes.views import detail

def home(request):
    """Displays the interactive map"""
    return render(request, "maps/map.html", {

    })

def lakes(request):
    """Return the KML for the lakes"""
    scale = int(request.GET['scale'])
    bbox = map(float, request.GET['bbox_limited'].split(","))

    lakes = NHDLake.objects.to_kml(scale=scale, bbox=bbox)
    return render(request, "maps/lakes.kml", {
        "lakes": lakes,
    })

def facilities(request):
    """Return the KML for the facilities"""
    bbox = map(float, request.GET['bbox_limited'].split(","))

    facilities = Facility.objects.to_kml(bbox=bbox)
    return render(request, "maps/facilities.kml", {
        "rows": facilities,
    })


def panel(request, reachcode):
    """
    Return the HTML for the information panel displayed when a lake is
    clicked on the map
    """
    return detail(request, reachcode, "maps/panel.html")

def search(request):
    """
    Return the HTML when a search is performed on the map
    """
    query = request.GET.get("query", "")
    lakes = NHDLake.objects.search(query)[:100]
    return render(request, "maps/_results.html", {"lakes": lakes})

