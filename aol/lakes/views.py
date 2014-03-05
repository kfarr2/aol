import csv
import string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from aol.documents.models import Document
from aol.photos.models import Photo
from .models import NHDLake, LakePlant

#@cache_page(60 * 15)
def listing(request, letter=None):
    """Display a list of all the lakes in the Atlas, with pagination"""
    lakes = None
    important_lakes = None
    non_important_lakes = None

    if letter is not None:
        letter = letter.upper()
        # defering the body field since it is unneeded and adds 100ms to the
        # page latency
        lakes = NHDLake.objects.by_letter(letter=letter).defer("body")

        paginator = Paginator(lakes, 100)
        page = request.GET.get('page')
        try:
            lakes = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            lakes = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            lakes = paginator.page(paginator.num_pages)

        # unfortunately, we have to create two iterables to simplify the template logic
        # one is for important lakes, the other is not non important lakes
        important_lakes = [l for l in lakes if l.is_important]
        non_important_lakes = [l for l in lakes if not l.is_important]

    return render(request, "lakes/listing.html", {
        "letters": string.ascii_uppercase,
        "lakes": lakes,
        "letter": letter,
        "important_lakes": important_lakes,
        "non_important_lakes": non_important_lakes,
    })

def detail(request, reachcode, template=None):
    """Display the detail view for an individual lake"""
    lake = get_object_or_404(NHDLake, reachcode=reachcode)
    photos = [p for p in Photo.objects.filter(lake=lake) if p.exists()]
    documents = Document.objects.filter(lake=lake).exclude(type=Document.MAP)
    maps = list(Document.objects.filter(lake=lake, type=Document.MAP))
    # the distinct clause with the listed fields is Postgres specific
    lake_plants = LakePlant.objects.filter(lake=lake).select_related("plant").distinct("plant__common_name", "plant__name", "observation_date")
    return render(request, template or "lakes/detail.html", {
        "lake": lake,
        "photos": photos,
        "documents": documents,
        "lake_plants": lake_plants,
        "maps": maps,
    })

def search(request):
    q = request.GET.get('q','')
    if "q" in request.GET:
        lakes = list(NHDLake.objects.search(query=q)[:100])
        if len(lakes) == 1:
            reachcode = lakes[0].reachcode
            return HttpResponseRedirect(reverse('lakes-detail', kwargs={'reachcode':reachcode}))

    return render(request, "lakes/results.html", {
        'lakes': lakes, 
        'query':q,
    })

def plants_csv(request, reachcode):
    """
    Export the plant data for a lake as a CSV
    """
    lake = get_object_or_404(NHDLake, reachcode=reachcode)
    lake_plants = LakePlant.objects.filter(lake=lake).select_related("plant")
    response = HttpResponse("", content_type="text/csv")
    response['content-disposition'] = "attachment; filename=%s" % (slugify(str(lake)) + ".csv")
    writer = csv.writer(response)
    writer.writerow([
        "Reachcode",
        "Lake Name",
        "Observation Date",
        "Plant Name",
        "Plant Common Name",
        "Noxious Weed Designation",
        "Is Native",
        "Source",
        "Survey Organization",
    ])
    for lake_plant in lake_plants:
        writer.writerow([
            str(lake.pk),
            str(lake),
            lake_plant.observation_date,
            lake_plant.plant.name,
            lake_plant.plant.common_name,
            lake_plant.plant.noxious_weed_designation,
            lake_plant.plant.is_native,
            lake_plant.source,
            lake_plant.survey_org
        ])

    return response

