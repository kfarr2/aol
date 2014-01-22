from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from aol.lakes.models import NHDLake

def home(request):
    """The homepage of the site"""
    return render(request, "home/home.html", {
    })
