from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import People, EntranceQR
from django.contrib import messages

@login_required
def index(request: HttpRequest):
    query = request.GET.get('q', '')
    people = People.objects.all().order_by('-register_date')

    if query:
        people = people.filter(
            Q(name__icontains=query) | 
            Q(father_name__icontains=query) |
            Q(nrc__icontains=query)
        )
    paginator = Paginator(people, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'people/index.html', context)

@login_required
def view_person(request: HttpRequest, id: str):
    if id:
        person = People.objects.get(id=id)
        print(person)
        return render(request, "people/view.html", {
            "person": person
        })
    
@login_required
def get_entrance_qr_view(request: HttpRequest, id: str):
    person = get_object_or_404(People, id=id)
    qr_record, created = EntranceQR.objects.get_or_create(people=person)

    if request.method == "POST":
        if qr_record.qr_image:
            qr_record.qr_image.delete(save=False)
        qr_record.qr_code_data = ""
        qr_record.save()
        return redirect('get_entrance_qr', id=person.id)

    return render(request, "people/qr.html", {
        "person": person,
        "qr": qr_record
    })

@login_required
def bulk_qr_view(request):
    ids = request.GET.getlist('ids')
    people = People.objects.all().order_by('name')
    
    if ids:
        people = people.filter(id__in=ids)
    for person in people:
        EntranceQR.objects.get_or_create(people=person)
    people_with_qr = people.prefetch_related('qr_codes')

    return render(request, "people/bulk_qr.html", {
        "people": people_with_qr,
    })

@login_required
def add_person_view(request: HttpRequest):
    if request.method == "POST":
        name = request.POST.get('name')
        father_name = request.POST.get('father_name')
        nrc = request.POST.get('nrc')
        address = request.POST.get('address')

        picture = request.FILES.get('picture')
        new_people = People.objects.create(
            name=name,
            father_name=father_name,
            nrc=nrc,
            address=address,
            picture=picture if picture else "" 
        )
        
        return redirect('people.index')

    return render(request, "people/add.html")

@login_required
def edit_person_view(request: HttpRequest, id: str):
    person = get_object_or_404(People, id=id)

    if request.method == "POST":
        person.name = request.POST.get('name')
        if request.FILES.get('edit_picture'):
            if person.picture:
                person.picture.delete(save=False)
            person.picture = request.FILES.get('edit_picture')
        person.nrc = request.POST.get('nrc')
        person.father_name = request.POST.get('father_name')
        person.address = request.POST.get('address')
        person.save()
        messages.success(request, f"Person '{person.name}' edited!")
        return redirect('people.view', id=person.id)

    return render(request, "people/edit.html", {
        "person": person
    })

@login_required
@require_POST
def delete_person(request, id):
    if request.method == "POST":
        people = get_object_or_404(People, id=id)
        people_name = people.name
        people.delete()
        messages.success(request, f"Person '{people.name}' has been deleted successfully.")
        
        return redirect('people.index')