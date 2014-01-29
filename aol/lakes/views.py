import string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse 
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Photo, Document, NHDLake, LakePlant

def listing(request, letter=None):
    """Display a list of all the lakes in the Atlas, with pagination"""
    letters = string.ascii_uppercase

    lakes = None
    if letter is not None:
        letter = letter.upper()
        lakes = list(NHDLake.objects.important_lakes(starts_with=letter))

    return render(request, "lakes/listing.html", {
        "letters": letters,
        "lakes": lakes,
        "letter": letter,
    })

def detail(request, reachcode, template=None):
    """Display the detail view for an individual lake"""
    lake = get_object_or_404(NHDLake, reachcode=reachcode)
    photos = [p for p in Photo.objects.filter(lake=lake) if p.exists()]
    documents = Document.objects.filter(lake=lake)
    lake_plants = LakePlant.objects.filter(lake=lake).select_related("plant")
    return render(request, template or "lakes/detail.html", {
        "lake": lake,
        "photos": photos,
        "documents": documents,
        "lake_plants": lake_plants,
    })

def search(request):
    q = request.GET.get('q','')
    if "q" in request.GET:
        lakes = list(NHDLake.objects.search(query=q))
        if len(lakes) == 1:
            reachcode = qs[0].reachcode
            return HttpResponseRedirect(reverse('lakes-detail', kwargs={'reachcode':reachcode}))
  
    return render(request, "lakes/results.html", {
        'lakes': lakes, 
        'query':q,
    })
