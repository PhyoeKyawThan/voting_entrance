from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Student, EntranceQR
from django.contrib import messages

@login_required
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

@login_required
def view_student(request: HttpRequest, student_id: str):
    if student_id:
        student = Student.objects.get(student_id=student_id)
        return render(request, "students/view.html", {
            "student": student
        })
    
@login_required
def get_entrance_qr_view(request: HttpRequest, student_id: str):
    student = get_object_or_404(Student, student_id=student_id)
    qr_record, created = EntranceQR.objects.get_or_create(student=student)

    if request.method == "POST":
        if qr_record.qr_image:
            qr_record.qr_image.delete(save=False)
        qr_record.qr_code_data = ""
        qr_record.save()
        return redirect('get_entrance_qr', student_id=student.student_id)

    return render(request, "students/qr.html", {
        "student": student,
        "qr": qr_record
    })

@login_required
def bulk_qr_view(request):
    semester = request.GET.get('semester')
    student_ids = request.GET.getlist('ids')
    students = Student.objects.all().order_by('roll_no')
    
    if semester:
        students = students.filter(current_semester=semester)
    if student_ids:
        students = students.filter(student_id__in=student_ids)
    for student in students:
        EntranceQR.objects.get_or_create(student=student)
    students_with_qr = students.prefetch_related('qr_codes')

    return render(request, "students/bulk_qr.html", {
        "students": students_with_qr,
        "semester": semester
    })

@login_required
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

@login_required
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
        messages.success(request, f"Student '{student.name}' edited!")
        return redirect('student.view', student_id=student.student_id)

    return render(request, "students/edit.html", {
        "student": student
    })

@login_required
@require_POST
def delete_student(request, student_id):
    if request.method == "POST":
        student = get_object_or_404(Student, student_id=student_id)
        student_name = student.name
        student.delete()
        messages.success(request, f"Student '{student_name}' has been deleted successfully.")
        
        return redirect('student.index')