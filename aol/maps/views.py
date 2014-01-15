from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from aol.lakes.models import NHDLake, Photo, Document, Facility
from aol.lakes.views import detail

def home(request):
    """Displays the interactive map"""
    lakes = NHDLake.objects.all()
    return render(request, "maps/map.html", {
        "lakes": lakes,
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
    return detail(request, reachcode, "maps/panel.html")
