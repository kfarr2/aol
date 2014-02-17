from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse 
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.flatpages.models import FlatPage
from aol.lakes.models import NHDLake, Plant 
from aol.photos.models import Photo
from aol.documents.models import Document
from .forms import LakeForm, FlatPageForm

@login_required
def listing(request):
    """List all the lakes that the admin can edit"""
    q = request.GET.get('q','')
    if "q" in request.GET:
        lakes = NHDLake.objects.search(query=q)
    else:
        lakes = None

    return render(request, "admin/listing.html", {
        "lakes": lakes,
        "q": q,
        "flatpages": FlatPage.objects.all(),
    })

@login_required
def edit_flatpage(request, pk=None):
    try:
        page = FlatPage.objects.get(pk=pk)
    except FlatPage.DoesNotExist:
        page = None

    if request.POST:
        form = FlatPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, "Page Editied")
            return HttpResponseRedirect(reverse("admin-listing"))
    else:
        form = FlatPageForm(instance=page)

    return render(request, "admin/edit_flatpage.html", {
        "form": form,
    })

@login_required
def edit_lake(request, reachcode):
    """The edit page for a lake"""
    lake = get_object_or_404(NHDLake, reachcode=reachcode)
    if request.POST:
        form = LakeForm(request.POST, instance=lake)
        if form.is_valid():
            form.save()
            messages.success(request, "Lake Edited")
            return HttpResponseRedirect(reverse("admin-edit-lake", args=(lake.pk,)))
    else:
        form = LakeForm(instance=lake)

    photos = Photo.objects.filter(lake=lake)
    documents = Document.objects.filter(lake=lake)

    return render(request, "admin/edit_lake.html", {
        "lake": lake,
        "form": form,
        "photos": photos,
        "documents": documents,
    })

