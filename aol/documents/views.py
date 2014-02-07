import mimetypes
import os
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse 
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from aol.lakes.models import NHDLake 
from .forms import DocumentForm 
from .models import Document

def download(request, document_id):
    """
    Allow the document to be downloaded with a friendly filename
    """
    document = get_object_or_404(Document, pk=document_id)
    ext = os.path.splitext(document.file.path)[-1].lower()
    filename = os.path.basename(document.file.path)
    if document.friendly_filename:
        filename = document.friendly_filename

    filename = filename.lower()

    if not filename.endswith(ext):
        filename += ext

    response = HttpResponse(document.file, content_type=mimetypes.guess_type(document.file.path))
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

@login_required
def edit(request, reachcode=None, document_id=None):
    """
    The add/edit page for a document. If a document_id is passed in, we edit. If the
    reachcode is passed in, we create
    """
    try:
        document = Document.objects.get(pk=document_id)
        lake = document.lake
    except Document.DoesNotExist:
        # create a new document with a foreign key to the lake
        lake = get_object_or_404(NHDLake, reachcode=reachcode)
        document = Document(lake=lake)

    if request.POST:
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document %s" % "Edited" if document_id else "Created")
            return HttpResponseRedirect(reverse("admin-edit-lake", args=(lake.pk,)))
    else:
        form = DocumentForm(instance=document)

    return render(request, "documents/edit.html", {
        "lake": lake,
        "document": document,
        "form": form,
    })

