from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from aol.lakes.models import NHDLake

def home(request):
    """The homepage of the site"""
    lakes = NHDLake.objects.all()
    return render(request, "home/home.html", {
        "lakes": lakes,
    })

def about(request):
    """The about page"""
    # maybe use flatpages for this instead?
    return render(request, "home/about.html", {

    })

def credits(request):
    """The credits page"""
    # maybe use flatpages for this instead?
    return render(request, "home/credits.html", {

    })

def photo_submissions(request):
    """The photo submissions page"""
    # maybe use flatpages for this instead?
    return render(request, "home/photo_submissions.html", {

    })
