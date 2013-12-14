from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from aol.lakes.models import Lake, Photo, Document, Facility

def home(request):
    """Displays the interactive map"""
    lakes = Lake.objects.all()
    return render(request, "maps/map.html", {
        "lakes": lakes,
    })

def lakes(request):
    """Return the KML for the lakes"""
    scale = int(request.GET['scale'])
    bbox = map(float, request.GET['bbox_limited'].split(","))

    lakes = Lake.objects.to_kml(scale=scale, bbox=bbox)
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
    lake = get_object_or_404(Lake, reachcode=reachcode)
    photos = Photo.objects.filter(lake=lake)
    documents = Document.objects.filter(lake=lake)
    return render(request, "maps/panel.html", {
        "lake": lake,
        "photos": photos,
        "documents": documents,
    })
