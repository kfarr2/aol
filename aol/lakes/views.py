from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse 
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Photo, Document, NHDLake

def listing(request, letter=None):
    """Display a list of all the lakes in the Atlas, with pagination"""
    lakes = list(NHDLake.objects.important_lakes())
    letters = sorted(set(str(lake)[0].upper() for lake in lakes if str(lake)))

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
    plants = lake.plants.all()
    return render(request, template or "lakes/detail.html", {
        "lake": lake,
        "photos": photos,
        "documents": documents,
        "plants": plants,
    })

def search(request):
    q = request.GET.get('q','')
    if "q" in request.GET:
        qs = NHDLake.objects.search(query=q)
        if qs.count() == 1:
            reachcode = qs[0].reachcode
            return HttpResponseRedirect(reverse('lakes-detail', kwargs={'reachcode':reachcode}))
  
    return render(request, "lakes/results.html", {
        'lakes': qs, 
        'query':q,
    })
