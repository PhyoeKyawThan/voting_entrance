from django.http.request import HttpRequest
from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Student

def index(request: HttpRequest):
    query = request.GET.get('q', '')
    semester_filter = request.GET.get('semester', '')
    
    students = Student.objects.all().order_by('-register_date')

    if query:
        students = students.filter(
            Q(name__icontains=query) | 
            Q(roll_no__icontains=query) |
            Q(student_number__icontains=query)
        )

    if semester_filter:
        students = students.filter(current_semester=semester_filter)
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'semester_filter': semester_filter,
    }
    return render(request, 'students/index.html', context)

def view_student(request: HttpRequest, student_id: str):
    if student_id:
        student = Student.objects.get(student_id=student_id)
        return render(request, "students/view.html", {
            "student": student
        })

def add_student_view(request: HttpRequest):
    if request.method == "POST":
        name = request.POST.get('name')
        father_name = request.POST.get('father_name')
        nrc = request.POST.get('nrc')
        birth_date = request.POST.get('birth_date')
        student_number = request.POST.get('student_number')
        roll_no = request.POST.get('roll_no')
        current_semester = request.POST.get('current_semester')
        phone_no = request.POST.get('phone_no')
        email = request.POST.get('email')
        address = request.POST.get('address')

        picture = request.FILES.get('picture')
        new_student = Student.objects.create(
            name=name,
            father_name=father_name,
            nrc=nrc,
            birth_date=birth_date,
            student_number=student_number,
            roll_no=roll_no,
            current_semester=current_semester,
            phone_no=phone_no,
            email=email,
            address=address,
            picture=picture if picture else "" 
        )
        
        return redirect('student.index')

    return render(request, "students/add.html")

def edit_student_view(request: HttpRequest, student_id: str):
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == "POST":
        student.name = request.POST.get('name')
        if request.FILES.get('edit_picture'):
            if student.picture:
                student.picture.delete(save=False)
            student.picture = request.FILES.get('edit_picture')
        student.student_number = request.POST.get('student_number')
        student.roll_no = request.POST.get('roll_no')
        student.current_semester = request.POST.get('current_semester')
        student.nrc = request.POST.get('nrc')
        student.father_name = request.POST.get('father_name')
        student.address = request.POST.get('address')
        student.phone_no = request.POST.get('phone_no')
        student.email = request.POST.get('email')
        
        student.save()
        
        return redirect('student.view', student_id=student.student_id)

    return render(request, "students/edit.html", {
        "student": student
    })

@require_POST
def delete_student_view(request: HttpRequest, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    student.delete()
    return redirect('student_list')