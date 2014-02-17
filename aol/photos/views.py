from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse 
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.flatpages.models import FlatPage
from aol.lakes.models import NHDLake
from .forms import PhotoForm 
from .models import Photo

@login_required
def edit(request, reachcode=None, photo_id=None):
    """
    The add/edit page for a photo. If a photo_id is passed in, we edit. If the
    reachcode is passed in, we create
    """
    try:
        photo = Photo.objects.get(pk=photo_id)
        lake = photo.lake
    except Photo.DoesNotExist:
        # create a new photo with a foreign key to the lake
        lake = get_object_or_404(NHDLake, reachcode=reachcode)
        photo = Photo(lake=lake)

    if request.POST:
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            form.save()
            messages.success(request, "Photo %s" % "Edited" if photo_id else "Created")
            return HttpResponseRedirect(reverse("admin-edit-lake", args=(lake.pk,)))
    else:
        form = PhotoForm(instance=photo)

    return render(request, "photos/edit.html", {
        "lake": lake,
        "photo": photo,
        "form": form,
    })

