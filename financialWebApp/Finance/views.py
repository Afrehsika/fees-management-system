from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import LEVEL, Student, Payment, LevelBill,Session
from django.contrib import messages
from django.db.models import Sum
from django.db import models
from django.urls import reverse
from vonage import Client as VonageClient
import vonage
from django.core.paginator import Paginator
import json
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.views.generic import TemplateView
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tablib import Dataset
from datetime import datetime
from django.template.loader import render_to_string
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch



# Initialize Vontage Client
vontage_client = VonageClient(key=VONTAGE_API_KEY, secret=VONTAGE_API_SECRET)
sms = vonage.Sms(vontage_client)



def summary_links(request):
    context = {
        'levels': LEVEL,
    }
    return render(request, 'summary_links.html', context)

def level_summary(request, level):
    sessions = Session.objects.all()
    context = {
        'level': level,
        'sessions': sessions,
    }
    return render(request, 'level_summary.html', context)


def session_summary_pdf(request, level, session_id):
    # Retrieve session object or return 404 if it doesn't exist
    session = get_object_or_404(Session, pk=session_id)

    try:
        # Retrieve level bill for the specified level and session
        level_bill = LevelBill.objects.get(level_name=level, academic_session=session)
    except LevelBill.DoesNotExist:
        # Return an error response if LevelBill doesn't exist for the given level and session
        return HttpResponse('LevelBill does not exist for the specified level and session.')

    # Retrieve students for the specified level
    students = Student.objects.filter(level=level)

    # Create a dictionary to store the total paid amount for each student
    total_paid_by_student = {student.id: student.payments.filter(session=session).aggregate(total_paid=models.Sum('paid_amount'))['total_paid'] or 0 for student in students}

    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="session_summary.pdf"'

    # Create a canvas
    p = canvas.Canvas(response, pagesize=letter)
    
    # Write your PDF content here using ReportLab
    p.drawString(100, 750, "AKROKERRI COLLEGE OF EDUCATION")
    p.drawString(100, 730, "Session Summary")
    p.drawString(100, 710, f"Session: {session}")
    p.drawString(100, 690, f"Level: {level}")

    y = 670
    for student in students:
        # Calculate total fees for the level for each student
        total_fees = level_bill.fees()

        # Calculate total paid amount for the student
        total_paid = total_paid_by_student.get(student.id, 0)

        # Calculate balance for the student
        balance = total_fees - total_paid

        # Draw student name and balance on the PDF
        p.drawString(100, y, f"Student: {student.name}, Balance: {balance}")
        y -= 20

    p.showPage()
    p.save()

    return response



def session_summary(request, level, session_id):
    # Retrieve session object or return 404 if it doesn't exist
    session = get_object_or_404(Session, pk=session_id)

    try:
        # Retrieve level bill for the specified level and session
        level_bill = LevelBill.objects.get(level_name=level, academic_session=session)
    except LevelBill.DoesNotExist:
        # Return an error response if LevelBill doesn't exist for the given level and session
        return render(request, 'error.html', {'message': 'LevelBill does not exist for the specified level and session.'})

    # Retrieve students for the specified level
    students = Student.objects.filter(level=level)

    # Initialize a list to store student balances
    student_balances = []

    # Calculate balance for each student
    for student in students:
        # Calculate total fees for the student's level
        total_fees = level_bill.fees()

        # Calculate total paid amount for the student for the specified session
        total_paid = student.payments.filter(session=session).aggregate(total_paid=models.Sum('paid_amount'))['total_paid'] or 0

        # Calculate balance for the student
        balance = total_fees - total_paid

        # Append student name and balance to the list of student balances
        student_balances.append({'student': student, 'balance': balance})

    context = {
        'session': session,
        'level': level,
        'student_balances': student_balances,
    }

    return render(request, 'balance_summary.html', context)




def session_view(request):
    session = Session.objects.all()
    context={
        "session":session
    }
    return render(request,"core/session_view.html",context)



@login_required(login_url="/authentication/login")
def session_add_view(request):
    if request.method == "POST":
        is_current_session = request.POST.get("is_current_session")
        session_name = request.POST.get("session")
        
        # Check if a session with the same name already exists
        if Session.objects.filter(session=session_name).exists():
            messages.error(request, "Session with this name already exists.")
            return redirect("finance:session_add")
        
        if is_current_session == "true":
            # Check if there is any existing current session and unset it
            existing_current_session = Session.objects.filter(is_current_session=True).first()
            if existing_current_session:
                existing_current_session.is_current_session = False
                existing_current_session.save()
        
        # Create a new session
        try:
            session = Session.objects.create(
                session=session_name,
                start_date=request.POST.get("start_date"),
                end_date=request.POST.get("end_date"),
                is_current_session=is_current_session == "true"
            )
            messages.success(request, "Session added successfully.")
        except IntegrityError:
            # Handle integrity error if session creation fails due to unique constraint violation
            messages.error(request, "Failed to add session. Please try again.")
        
        return redirect("finance:session")
    
    return render(request, "core/session_add.html")


@login_required(login_url="/authentication/login")
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        is_current_session = request.POST.get("is_current_session")
        if is_current_session == "true":
            # Check if there is any existing current session and unset it
            existing_current_session = Session.objects.filter(is_current_session=True).first()
            if existing_current_session:
                existing_current_session.is_current_session = False
                existing_current_session.save()
        
        session.session = request.POST.get("session")
        session.start_date = request.POST.get("start_date")
        session.end_date = request.POST.get("end_date")
        session.is_current_session = is_current_session == "true"
        session.save()
        messages.success(request, "Session updated successfully.")
        return redirect("finance:session")
    
    return render(request, "core/session_update.html", {"session": session})



@login_required(login_url="/authentication/login")
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.is_current_session:
        messages.error(request, "You cannot delete the current session.")
        return redirect("finance:session")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted.")
    return redirect("finance:session")

@csrf_exempt
def search_student(request):
    if request.method == "POST":
        search_str = json.loads(request.body).get('searchText', '')

        # Filter students based on search query
        students = Student.objects.filter(
            name__istartswith=search_str) | Student.objects.filter(
                student_id__startswith=search_str) | Student.objects.filter(
                    index_number__startswith=search_str) | Student.objects.filter(
                        reference_number__startswith=search_str)

        # Create an empty list to store serialized student data
        serialized_students = []

        # Iterate over filtered students to calculate total paid amount and balance
        for student in students:
            # Retrieve the current session
            current_session = Session.objects.filter(is_current_session=True).first()

            # Calculate total amount paid by the student for the current session
            total_paid = Payment.objects.filter(student=student, session=current_session).aggregate(total=models.Sum('paid_amount'))['total'] or 0
            
            # Find the corresponding level bill for the student's level and the current session
            level_bill = LevelBill.objects.filter(level_name=student.level, academic_session=current_session).first()
            
            if level_bill:
                # Calculate the balance if level bill exists
                balance = level_bill.fees() - total_paid
            else:
                balance = 0

            # Serialize student data
            serialized_student = {
                'id': student.pk,
                'name': student.name,
                'student_id': student.student_id,
                'index_number': student.index_number,
                'level': student.level,
                'balance': balance,
                'total_fees': level_bill.fees() if level_bill else 0,
                'total_paid': total_paid,
            }

            # Append serialized student to the list
            serialized_students.append(serialized_student)

        # Return JSON response with serialized student data
        return JsonResponse(serialized_students, safe=False)
    else:
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

@login_required(login_url="/authentication/login")
def levelBillView(request):
    current_session = Session.objects.filter(is_current_session=True).first()
    billing = LevelBill.objects.filter(academic_session=current_session)
    context = {
        "billing": billing
    }
    return render(request, "finance/bill.html", context)


@login_required(login_url="/authentication/login")
def addlevelbill(request):
    if request.method == "POST":
        level = request.POST['level']
        academic_fees = request.POST['academic']
        student_fees = request.POST['student']
        exams_fees = request.POST['exams']
        session_name = request.POST['session'] 
        
       
        session_instance = get_object_or_404(Session, session=session_name)

        LevelBill.objects.create(
            level_name=level,
            academic_fees=academic_fees,
            student_fees=student_fees,
            exams_fees=exams_fees,
            academic_session=session_instance
        )
        messages.success(request, "Fees is added successfully")
        return redirect("finance:bill")
    else:
       
        sessionq = Session.objects.all()
        context = {
            'level': LEVEL,
            'sessionq': sessionq
        }
        return render(request, "finance/add_bill.html", context)


@login_required(login_url="/authentication/login")
def editlevelbill(request, level_id):
    try:
        level_bill = LevelBill.objects.get(id=level_id)
        sessionq = Session.objects.all()
    except LevelBill.DoesNotExist:
        messages.error(request, "Level bill not found")
        return redirect("finance:bill")

    if request.method == "POST":
        level = request.POST['level']
        academic_fees = request.POST['academic']
        student_fees = request.POST['student']
        exams_fees = request.POST['exams']
        session = request.POST['session']
        
        session_instance = get_object_or_404(Session, session=session)
        # Update the level bill object
        level_bill.level_name = level
        level_bill.academic_fees = academic_fees
        level_bill.student_fees = student_fees
        level_bill.exams_fees = exams_fees
        level_bill.academic_session = session_instance
        level_bill.save()

        messages.success(request, "Fees is updated successfully")
        return redirect("finance:bill")  # Redirect to the appropriate page after editing

    context = {
        'level_bill': level_bill,
        'level': LEVEL,
        "values": level_bill,
        'sessionq': sessionq
    }
    return render(request, "finance/edit_bill.html", context)




@login_required(login_url="/authentication/login")
def paymentView(request):
    current_session = Session.objects.filter(is_current_session=True).first()
    students = Student.objects.all()
    level_bills = LevelBill.objects.filter(academic_session=current_session)
    paginator = Paginator(students, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for student in page_obj:
        # Calculate total amount paid by the student for the current session
        total_paid_current_session = Payment.objects.filter(student=student, session=current_session).aggregate(total=models.Sum('paid_amount'))['total'] or 0
        
        # Initialize total balance for previous sessions
        total_balance_previous_sessions = 0
        
        # Iterate over sessions that are not the current session
        previous_sessions = Session.objects.filter(is_current_session=False)
        for session in previous_sessions:
            # Calculate total amount paid by the student for the session
            total_paid_session = Payment.objects.filter(student=student, session=session).aggregate(total=models.Sum('paid_amount'))['total'] or 0
            
            # Find the corresponding level bill for the student's level and session
            level_bill = LevelBill.objects.filter(level_name=student.level, academic_session=session).first()
            if level_bill:
                # Calculate the balance if level bill exists
                session_balance = level_bill.fees() - total_paid_session
                total_balance_previous_sessions += session_balance  # Accumulate positive balances only
            
        # Find the corresponding level bill for the student's level in the current session
        level_bill_current_session = level_bills.filter(level_name=student.level).first()
        if level_bill_current_session:
            # Calculate the balance for the current session
            balance_current_session = level_bill_current_session.fees() + total_balance_previous_sessions - total_paid_current_session
            student.balance = balance_current_session  # Ensure balance is not negative
            student.total_fees = level_bill_current_session.fees() + total_balance_previous_sessions  # Add total balance for previous sessions
            student.total_paid = total_paid_current_session  # Include total paid in the student object
            student.level_bill = level_bill_current_session  # Assign level bill to the student
        else:
            # If no level bill found for the current session, set balance, total fees, and level bill to None
            student.balance = 0
            student.total_fees = total_balance_previous_sessions  # Only add total balance for previous sessions
            student.total_paid = total_paid_current_session  # Include total paid in the student object
            student.level_bill = None


    context ={
        "page_obj": page_obj
    }
    return render(request, "finance/payment.html", context)

@login_required(login_url="/authentication/login")
def index(request):
    current_session = Session.objects.filter(is_current_session=True).first()
    students = Student.objects.all()
    level_bills = LevelBill.objects.filter(academic_session=current_session)
    paginator = Paginator(students, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for student in page_obj:
        # Calculate total amount paid by the student for the current session
        total_paid_current_session = Payment.objects.filter(student=student, session=current_session).aggregate(total=models.Sum('paid_amount'))['total'] or 0
        
        # Initialize total balance for previous sessions
        total_balance_previous_sessions = 0
        
        # Iterate over sessions that are not the current session
        previous_sessions = Session.objects.filter(is_current_session=False)
        for session in previous_sessions:
            # Calculate total amount paid by the student for the session
            total_paid_session = Payment.objects.filter(student=student, session=session).aggregate(total=models.Sum('paid_amount'))['total'] or 0
            
            # Find the corresponding level bill for the student's level and session
            level_bill = LevelBill.objects.filter(level_name=student.level, academic_session=session).first()
            if level_bill:
                # Calculate the balance if level bill exists
                session_balance = level_bill.fees() - total_paid_session
                total_balance_previous_sessions += session_balance  # Accumulate positive balances only
            
        # Find the corresponding level bill for the student's level in the current session
        level_bill_current_session = level_bills.filter(level_name=student.level).first()
        if level_bill_current_session:
            # Calculate the balance for the current session
            balance_current_session = level_bill_current_session.fees() + total_balance_previous_sessions - total_paid_current_session
            student.balance = balance_current_session  # Ensure balance is not negative
            student.total_fees = level_bill_current_session.fees() + total_balance_previous_sessions  # Add total balance for previous sessions
            student.total_paid = total_paid_current_session  # Include total paid in the student object
            student.level_bill = level_bill_current_session  # Assign level bill to the student
        else:
            # If no level bill found for the current session, set balance, total fees, and level bill to None
            student.balance = 0
            student.total_fees = total_balance_previous_sessions  # Only add total balance for previous sessions
            student.total_paid = total_paid_current_session  # Include total paid in the student object
            student.level_bill = None

    context ={
        "page_obj": page_obj
    }
    return render(request, "finance/index.html", context)


@login_required(login_url="/authentication/login")
def add_students(request):
    context={
        "level": LEVEL,
        "values": request.POST
    }

    if request.method == "GET":
        return render(request, "finance/add_students.html", context)

    if request.method == "POST":
        name = request.POST['name']
        student_id = request.POST['student_id']
        index_number = request.POST['index_number']
        reference_number = request.POST['reference_number']
        phone = request.POST['phone']
        email = request.POST['email']
        level = request.POST['level']


        if not student_id:
            student_id = None

        if not index_number:
            index_number = None

        if not reference_number:
            reference_number = None

        if not name:
            messages.error(request, "Name is required")
            return render(request, "finance/add_students.html", context)
        elif student_id is None and index_number is None and reference_number is None:
            messages.error(request, "At least one of Student ID, Index Number, or Reference Number is required")
            return render(request, "finance/add_students.html", context)
        elif not phone:
            messages.error(request, "Phone number is required")
            return render(request, "finance/add_students.html", context)
        elif level not in dict(LEVEL).keys():
            messages.error(request, "Invalid level selected")
            return render(request, "finance/add_students.html", context)


        Student.objects.create(name=name, student_id=student_id, index_number=index_number, reference_number=reference_number,
                               phone=phone, email=email, level=level)
        messages.success(request, "Student saved successfully")
        return redirect("finance:student")

@login_required(login_url="/authentication/login")   
def student_edit(request, name):
    try:
        student = Student.objects.get(name=name)
    except Student.DoesNotExist:
        messages.error(request, "Student not found")
        return redirect("finance:student")

    if request.method == "POST":
        form_data = request.POST
        form_name = form_data.get('name')
        form_student_id = form_data.get('student_id')
        form_index_number = form_data.get('index_number')
        form_reference_number = form_data.get('reference_number')
        form_phone = form_data.get('phone')
        form_email = form_data.get('email')
        form_level = form_data.get('level')

        # Validation checks
        if not form_name:
            messages.error(request, "Name is required")
            return redirect("finance:edit_student", name=name)
        elif not (form_student_id or form_index_number or form_reference_number):
            messages.error(request, "At least one of Student ID, Index Number, or Reference Number is required")
            return redirect("finance:edit_student", name=name)
        elif not form_phone:
            messages.error(request, "Phone number is required")
            return redirect("finance:edit_student", name=name)
        elif form_level not in dict(LEVEL).keys():
            messages.error(request, "Invalid level selected")
            return redirect("finance:edit_student", name=name)

        # Update student object with form data
        student.name = form_name
        student.student_id = form_student_id
        student.index_number = form_index_number
        student.reference_number = form_reference_number
        student.phone = form_phone
        student.email = form_email
        student.level = form_level
        student.save()
        
        messages.success(request, "Student Profile Updated successfully")
        return redirect("finance:student")

    context ={
        'student': student,
        'level': LEVEL,
        'values':student
    }
    return render(request, "finance/edit_student.html", context)



@login_required(login_url="/authentication/login")
def process_payment(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        messages.error(request, "Student not found")
        return redirect("finance:student")

    if request.method == "POST":
        try:
            # Retrieve the current session
            current_session = Session.objects.get(is_current_session=True)
            
            # Retrieve the level bill for the student's level in the current session
            level_bill = LevelBill.objects.get(level_name=student.level, academic_session=current_session)
        except LevelBill.DoesNotExist:
            messages.error(request, "Level bill not found")
            return redirect("finance:bill")
        except Session.DoesNotExist:
            messages.error(request, "Current session not found")
            return redirect("finance:bill")

        paid_amount = float(request.POST.get('paid_amount'))

        # Calculate total paid amount for all previous sessions
        total_paid_previous_sessions = Payment.objects.filter(student=student, session__lt=current_session).aggregate(total=models.Sum('paid_amount'))['total'] or 0

        # Calculate the old balance by subtracting the total paid amount for previous sessions from the total fees for previous sessions
        old_balance = total_paid_previous_sessions - level_bill.fees()

        # Add the old balance to the total fees for the current session to get the new total fees
        new_total_fees = level_bill.fees() + old_balance

        # Check if a payment record already exists for the student
        existing_payment = Payment.objects.filter(student=student).first()

        if existing_payment:
            # If payment record exists, update the payment amount
            existing_payment.paid_amount += paid_amount
            existing_payment.save()
        else:
            # If no payment record exists, create a new payment record
            payment = Payment.objects.create(
                student=student,
                levelBilling=level_bill,
                session=current_session,  # Set the session for the payment
                paid_amount=paid_amount,
                bank_of_payment=request.POST.get('bank_of_payment'),
                draft_no=request.POST.get('draft_no')
            )

        # Update student balance
        student.payment_balance = new_total_fees
        student.save()

        # Send SMS notification using Vontage
        message = f"Dear {student.name}, your payment of GHS{paid_amount} as your college fees, has been successfully received."
        send_sms(student.phone, message)

         # Generate PDF receipt
        receipt_data = {
            'student': student,
            'session': current_session,
            'payment_amount': paid_amount,
            'level_bill': level_bill
        }
        pdf = generate_receipt_pdf(receipt_data)
       
    
        # Send PDF as response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="receipt.pdf"'
        messages.success(request, "Payment processed successfully") 
        return response
    else:
        return render(request, "finance/payment_form.html", {"student": student})
  
def generate_receipt_pdf(data):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Define styles
    styles = getSampleStyleSheet()
    receipt_style = ParagraphStyle(
        name='Receipt',
        parent=styles['Normal'],
        fontSize=12,
        textColor='black',
        leftIndent=inch,
        rightIndent=inch,
        spaceAfter=12,
    )

    # Build content
    content = []

    # Add image
    image_path = 'static/img/ARCE.jpg'  # Change this to the path of your image
    logo = Image(image_path, width=2*inch, height=2*inch)
    content.append(logo)

    # Add title
    title_text = '<b>AKROKERRI COLLEGE OF EDUCATION</b>'
    title = Paragraph(title_text, styles['Title'])
    content.append(title)

    # Add payment receipt title
    receipt_title = '<b>Payment Receipt</b>'
    content.append(Paragraph(receipt_title, styles['Title']))

    # Add student details
    details = [
        f"<b>Student Name:</b> {data['student'].name}",
        f"<b>Index Number:</b> {data['student'].index_number}",
        f"<b>Level:</b> {data['student'].level}",
        f"<b>Amount Paid:</b> GHS {data['payment_amount']}",
        f"<b>Payment Date:</b> {data['session'].start_date} - {data['session'].end_date}",
       
    ]
    
    # Check if 'bank_of_payment' key exists in data dictionary
    if 'bank_of_payment' in data:
        details.append(f"<b>Bank of Payment:</b> {data['bank_of_payment']}")
    
    # Check if 'draft_no' key exists in data dictionary
    if 'draft_no' in data:
        details.append(f"<b>Draft No:</b> {data['draft_no']}")

    for detail in details:
        content.append(Paragraph(detail, receipt_style))

    # Build PDF
    doc.build(content)

    # Get PDF data
    pdf_buffer.seek(0)
    pdf = pdf_buffer.getvalue()
    pdf_buffer.close()

    return pdf

def send_sms(phone_number, message):
    try:
        sms.send_message({
            'from': VONTAGE_PHONE_NUMBER,
            'to': phone_number,
            'text': message
        })
        print("SMS sent successfully.")
    except Exception as e:
        
        print(f"Failed to send SMS: {str(e)}")
        


def import_excel(request):
    if request.method == 'POST':
        dataset = Dataset()
        new_data = request.FILES['my_file']
        imported_data = dataset.load(new_data.read(), format='xlsx')

        for data in imported_data:
            session_name = data[0]
            start_date = datetime.strptime(data[1].strftime('%Y-%m-%d'), '%Y-%m-%d') if data[1] else None
            end_date = datetime.strptime(data[2].strftime('%Y-%m-%d'), '%Y-%m-%d') if data[2] else None
            is_current = False if not data[3] else True 
            
            session, _ = Session.objects.get_or_create(session=session_name,
                                                        defaults={
                                                            'start_date': start_date,
                                                            'end_date': end_date,
                                                            'is_current_session': is_current
                                                        })

            student_name = data[4]
            student_id = data[5]
            index_number = data[6]
            reference_number = data[7]
            phone = data[8]
            email = data[9]
            level = data[10]
            balance = data[11]

            student, _ = Student.objects.get_or_create(name=student_name,
                                                        defaults={
                                                            'student_id': student_id,
                                                            'index_number': index_number,
                                                            'reference_number': reference_number,
                                                            'phone': phone,
                                                            'email': email,
                                                            'level': level,
                                                            'payment_balance': balance
                                                        })

            
            academic_fee = data[12]
            student_fee = data[13]
            exams_fee = data[14]

            level_bill, _ = LevelBill.objects.get_or_create(level_name=level,
                                                             academic_session=session,
                                                             defaults={
                                                                 'academic_fees': academic_fee,
                                                                 'student_fees': student_fee,
                                                                 'exams_fees': exams_fee
                                                             })
            amount_paid = data[15]
            bank = data[16]
            payment_date = datetime.strptime(data[17].strftime('%Y-%m-%d'), '%Y-%m-%d') if data[17] else datetime.now()  # Use current date if no date provided

            payment, _ = Payment.objects.get_or_create(student=student,
                                                        levelBilling=level_bill,
                                                        session=session,
                                                        defaults={
                                                            'paid_amount': amount_paid,
                                                            'bank_of_payment': bank,
                                                            'date': payment_date
                                                        })


          
    return render(request, "import.html")

