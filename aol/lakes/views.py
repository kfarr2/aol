from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse 
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Photo, Document, NHDLake

def listing(request):
    """Display a list of all the lakes in the Atlas, with pagination"""
    lakes = NHDLake.objects.all().order_by("gnis_name")

    return render(request, "lakes/listing.html", {
        "lakes": lakes,
    })

def detail(request, reachcode):
    """Display the detail view for an individual lake"""
    lake = get_object_or_404(NHDLake, reachcode=reachcode)
    photos = Photo.objects.filter(lake=lake)
    documents = Document.objects.filter(lake=lake)
    plants = lake.plants.all()
    return render(request, "lakes/detail.html", {
        "lake": lake,
        "photos": photos,
        "documents": documents,
        "plants": plants,
    })

def search(request):
    q = request.GET.get('q','')
    qs = NHDLake.objects.filter(title__icontains=q)
    if not qs:
        return render(request, "lakes/results.html", {
            'error': True, 'query': q})
    elif qs.count() == 1:
        reachcode = qs[0].reachcode
        return HttpResponseRedirect(reverse('lakes-detail', kwargs={'reachcode':reachcode}))
  

    return render(request, "lakes/results.html", {
        'lakes': qs, 
        'query':q,
        })
