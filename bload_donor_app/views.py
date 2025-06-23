# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from .models import * # This covers all models, so specific model imports are removed
from math import radians, cos, sin, asin, sqrt
from datetime import date, timedelta
from django.core.mail import send_mass_mail
from .forms import MassNotificationForm, DonationDriveForm  # Combined form imports
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import login
from django.contrib.auth import logout  
from django.db.models import Count
from .ml_model.predictor import predict_donation
from django.db.models.functions import TruncMonth
from django.db.models import Count
import numpy as np
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from math import radians, cos, sin, asin, sqrt
from datetime import date, timedelta, datetime, time
from .models import Donor, Collector, DonationDrive, DonationAppointment
from .decorators import donor_login_required, collector_login_required


# handling the loggin sessions using custom user 
from functools import wraps

# this is collector login
def collector_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('collector_id'):
            return redirect('collector_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def urgency_banner(request):
    banner = UrgencyBanner.objects.filter(is_active=True).first()
    return {'urgency_banner': banner}

# Home page view
def index(request):
    context = {
        'faqs': FAQ.objects.all(),
        # 'tomorrow_date': (date.today() + timedelta(days=1)).isoformat(),
    }
    request.session.flush()
    return render(request, 'index.html', context)

def role_selection(request):
    return render(request, 'role.html')

# donor user of the system
# Step 1: Collector registration form
@csrf_exempt
def register_donor(request):
    blood_types = [choice[0] for choice in Donor.BLOOD_TYPE_CHOICES]
    time_slots = '09:00 10:30 12:00 13:30 15:00 16:30 18:00 19:30'.split()

    if request.method == 'POST':
        has_donated_before = request.POST.get('donatedBefore') == 'Yes'
        last_donation_input = request.POST.get('lastDonation') or None

        if has_donated_before:
            if not last_donation_input:
                messages.error(request, "⚠️ Please provide the date of your previous donation.")
                return render(request, 'registdonor.html', {
                    'blood_types': blood_types,
                    'time_slots': time_slots,
                })

            try:
                last_donation_date = date.fromisoformat(last_donation_input)
                if last_donation_date > date.today():
                    messages.error(request, "⚠️ Last donation date can't be in the future.")
                    return render(request, 'registdonor.html', {
                        'blood_types': blood_types,
                        'time_slots': time_slots,
                    })
            except ValueError:
                messages.error(request, "⚠️ Invalid date format.")
                return render(request, 'registdonor.html', {
                    'blood_types': blood_types,
                    'time_slots': time_slots,
                })
        else:
            last_donation_date = None

        # === Save donor
        donor = Donor.objects.create(
            first_name=request.POST['firstName'],
            last_name=request.POST['lastName'],
            phone=request.POST['phoneNumber'],
            email=request.POST['email'],
            dob=request.POST['dob'],
            gender=request.POST['gender'],
            blood_type=request.POST['bloodType'],
            province=request.POST['province'],
            district=request.POST['district'],
            sector=request.POST['sector'],
            donation_time=request.POST['donationTime'],
            additional_info=request.POST.get('additionalInfo', ''),
            has_donated_before=has_donated_before,
            last_donation_before_registration=last_donation_date,
        )

        # ✅ Save past donation to appointment table (historical record)
        if has_donated_before and last_donation_date:
            from bload_donor_app.models import DonationAppointment
            DonationAppointment.objects.create(
                donor=donor,
                appointment_date=last_donation_date,
                appointment_time=time(9, 0),  # Assume 9:00 AM as placeholder
                selected_center='Previously Donated (Unregistered)',
                confirmed=True,
                has_donated_before=False,  # Since it's the first one
            )

        request.session['donor_id'] = donor.id
        return redirect('credential')

    return render(request, 'registdonor.html', {
        'blood_types': blood_types,
        'time_slots': time_slots,
    })

# Step 2: Credentials form

def credential(request):
    donor_id = request.session.get('donor_id')

    # Redirect if donor is not in session
    if not donor_id:
        return redirect('index')

    donor = get_object_or_404(Donor, id=donor_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'Credential.html')

        if Donor.objects.filter(username=username).exclude(id=donor_id).exists():
            messages.error(request, "This username is already taken. Please choose another one.")
            return render(request, 'Credential.html')

        # Password must contain at least one lowercase, uppercase, digit, special character, and be 8+ characters long
        password_regex = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        )
        if not password_regex.match(password):
            messages.error(request, "Password does not meet the required strength.")
            return render(request, 'Credential.html')

        # Save credentials
        donor.username = username
        donor.password = make_password(password)
        donor.save()

        return redirect('complete')
    return render(request, 'Credential.html')
# Step 3: Completion screen
def complete(request):
    # Check if the user is a donor
    donor_id = request.session.get('donor_id')
    if donor_id:
        donor = get_object_or_404(Donor, id=donor_id)
        formatted_id = f"LS-2025-{str(donor.id).zfill(4)}"

        # Clear donor session ID after rendering
        request.session.pop('donor_id', None)

        return render(request, 'Complete.html', {
            'donor': donor,
            'formatted_id': formatted_id,
        })

    # Check if the user is a collector
    collector_id = request.session.get('collector_id')
    if collector_id:
        collector = get_object_or_404(Collector, id=collector_id)
        formatted_id = f"LSC-2025-{str(collector.id).zfill(4)}"

        # Clear collector session ID after rendering
        request.session.pop('collector_id', None)

        return render(request, 'Complete.html', {
            'collector': collector,
            'formatted_id': formatted_id,
        })

    # If neither donor nor collector session is found, redirect to the home or role selection
    return redirect('register_donor') # or 'ridirecting to register_donor' or 'index' based on your flow

# Donor login page view (now handles form and logic)
def donor_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            donor = Donor.objects.get(username=username)
            
            if check_password(password, donor.password):
                # Ensure session is active
                if not request.session.session_key:
                    request.session.create()

                # Set donor session info
                if not request.session.session_key:
                 request.session.create()

                request.session['donor_id'] = donor.id
                request.session['donor_username'] = donor.username
                messages.success(request, "Login successful!")
                return redirect('donor')
            else:
                messages.error(request, "Incorrect password.")
                print("Incorrect password branch")
                

        except Donor.DoesNotExist:
            messages.error(request, "Username does not exist.")

    return render(request, 'logindon.html')

# ==================================start of donor view========================================
# Haversine function for distance calculation
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in kilometers
    return c * r

#==================================== Donor view===============================================================
@donor_login_required
def donor(request):
    donor = get_object_or_404(Donor, id=request.session.get('donor_id'))
    context = {
        'donor': donor,
        'faqs': FAQ.objects.all(),
        'tomorrow_date': (date.today() + timedelta(days=1)).isoformat(),
    }
    return render(request, 'donor.html', context)

#============================================end of donor view==============================================

#=======================================scheduling appointment view========================================================


@require_POST
def schedule_appointment(request):
    try:
        selected_date = request.POST.get('appointment_date')
        selected_time = request.POST.get('appointment_time')
        location_coords = request.POST.get('location')  # format: "lat,lon"
        selected_drive_id = request.POST.get('drive_id')

        donor_id = request.session.get('donor_id')
        donor = Donor.objects.filter(id=donor_id).first()

        if donor and selected_date and selected_time and location_coords:
            user_lat, user_lon = map(float, location_coords.split(','))

            nearest_collector = None
            min_distance = float('inf')

            for collector in Collector.objects.exclude(location_coordinates__isnull=True).exclude(location_coordinates=''):
                try:
                    col_lat, col_lon = map(float, collector.location_coordinates.split(','))
                    distance = haversine(user_lon, user_lat, col_lon, col_lat)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_collector = collector
                except ValueError:
                    continue

            if not nearest_collector:
                messages.error(request, '❌ No valid collection centers found.')
                return JsonResponse({'error': '❌ No valid collection centers found.'}, status=404)

            # Ensure the drive exists and is associated with the nearest collector
            drive = DonationDrive.objects.filter(id=selected_drive_id, collector=nearest_collector).first()
            if not drive:
                messages.error(request, '❌ The selected donation drive is not available at the nearest center.')
                return JsonResponse({'error': '❌ The selected donation drive is not available at the nearest center.'}, status=400)

            # ✅ Determine if donor has donated before
            # has_donated_before = donor.appointments.exists()
            has_donated_before = donor.appointments.exists() or donor.has_donated_before


            # Save the appointment
            DonationAppointment.objects.create(
                donor=donor,
                collector=nearest_collector,
                drive=drive,
                appointment_date=selected_date,
                appointment_time=selected_time,
                selected_center=nearest_collector.facility_name,
                confirmed=True,
                donor_coordinates=location_coords,
                collector_coordinates=nearest_collector.location_coordinates,
                has_donated_before=has_donated_before,
            )

            # Send confirmation email
            subject = 'Your Blood Donation Appointment is Confirmed!'
            message = (
                f"Dear {donor.full_name},\n\n"
                f"Thank you for scheduling your blood donation appointment.\n\n"
                f"Here are your appointment details:\n"
                f"Date: {selected_date}\n"
                f"Time: {selected_time}\n"
                f"Collection Center: {nearest_collector.facility_name}\n"
                f"Location Details: {nearest_collector.district}, {nearest_collector.province}\n\n"
                f"You will be notified of any changes to your scheduled appointment.\n\n"
                f"We appreciate your contribution to saving lives!\n\n"
                f"Sincerely,\nRBC Blood Donation Team"
            )
            from_email = 'dboringo3@gmail.com'
            recipient_list = [donor.email]

            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                messages.success(request, '✅ Appointment scheduled successfully and confirmation email sent!')
            except Exception as email_e:
                messages.warning(request, f'✅ Appointment scheduled, but failed to send confirmation email: {email_e}')
                print(f"Error sending email: {email_e}")

            return redirect('index')  # or your actual homepage/dashboard view

        else:
            messages.error(request, '❌ Please fill in all required fields.')
            return JsonResponse({'error': '❌ Please fill in all required fields.'}, status=400)

    except Exception as e:
        messages.error(request, f"❌ An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': f"❌ Error: {str(e)}"}, status=500)   

def donor_password_reset_request(request):
    return render(request, 'logindon.html')

#=============================end of make appointment view =============================================

#==================================start of collector view==================================================
# =================================Collector registration page view (now handles form and logic)============
@csrf_exempt
def register_collector(request):
    if request.method == 'POST':
        # Extract form data
        facility_name = request.POST.get('facilityName')
        facility_type = request.POST.get('facilityType')
        license_number = request.POST.get('licenseNumber')
        registration_number = request.POST.get('registrationNumber')  # Optional
        province = request.POST.get('province')
        district = request.POST.get('district')
        location = request.POST.get('location')  # Optional
        location_coordinates = request.POST.get('locationCoordinates')  # Optional
        contact_person = request.POST.get('contactPerson')
        position = request.POST.get('position')
        phone = request.POST.get('phoneNumber')
        email = request.POST.get('emailAddress')
        operating_hours = request.POST.get('operatingHours')  # Optional
        staff_capacity = request.POST.get('staffCapacity')  # Optional
        additional_info = request.POST.get('additionalInfo')  # Optional
        terms_agreed = request.POST.get('terms')

        # Required fields check
        required_fields = [
            facility_name, facility_type, license_number,
            province, district, contact_person, position,
            phone, email, terms_agreed
        ]

        if not all(required_fields):
            messages.error(request, "Please fill in all required fields.")
            return redirect('register_collector')

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email format.")
            return redirect('register_collector')

        # Check for duplicate email
        if Collector.objects.filter(email=email).exists():
            messages.error(request, "A facility with this email already exists.")
            return redirect('register_collector')

        # Save to database
        collector = Collector.objects.create(
            facility_name=facility_name,
            facility_type=facility_type,
            license_number=license_number,
            registration_number=registration_number,
            province=province,
            district=district,
            location=location,
            location_coordinates=location_coordinates,
            contact_person=contact_person,
            position=position,
            phone=phone,
            email=email,
            #operating_hours=operating_hours,
            staff_capacity=staff_capacity,
            additional_info=additional_info
        )

        # Store ID for next step (if needed)
        request.session['collector_id'] = collector.id

        # Redirect to login or confirmation page
        return redirect('collector_login')  # or 'collector_success' if you have a success page
    

    return render(request, 'registcollector.html')

# Collector login page view (now handles form and logic)
@csrf_exempt
def collector_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Check if the collector exists
        try:
            collector = Collector.objects.get(username=username)
        except Collector.DoesNotExist:
            messages.error(request, "Username does not exist.")
            return redirect('collector_login')

        # Check password
        if not check_password(password, collector.password):
            messages.error(request, "Incorrect password.")
            return redirect('index')

        # Successful login: store collector info in session
        request.session['collector_id'] = collector.id
        request.session['collector_username'] = collector.username
        messages.success(request, f"Welcome, {collector.facility_name}!")
        return redirect('collector')

    return render(request, 'logincolle.html')


def change_password(request):
    collector_id = request.session.get('collector_id')
    
    if not collector_id:
        messages.error(request, "You must be logged in to change your password.")
        return redirect('collector_login')

    collector = Collector.objects.get(id=collector_id)

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'change_password.html')

        password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        if not password_regex.match(password):
            messages.error(request, "Password must be at least 8 characters, include uppercase, lowercase, digit, and special character.")
            return render(request, 'change_password.html')

        collector.password = make_password(password)
        collector.must_change_password = False  # Clear the flag after change
        collector.save()

        messages.success(request, "Password updated successfully!")
        return redirect('collector')  # Redirect to collector dashboard or login

    return render(request, 'change_password.html')

#================================== Collector dashboard view ==================================================
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Max
from django.db.models.functions import TruncMonth
from datetime import date, timedelta
import numpy as np

from bload_donor_app.models import Collector, DonationDrive, Donor, DonationAppointment
from bload_donor_app.ml_model.predictor import predict_donation

def months_since(date_obj):
    if not date_obj:
        return 0
    today = date.today()
    return (today.year - date_obj.year) * 12 + (today.month - date_obj.month)
@collector_login_required
def collector(request):
    from django.core.mail import send_mail
    from django.conf import settings

    today = date.today()
    two_days_later = today + timedelta(days=2)
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())

    collector_id = request.session.get('collector_id')
    collector = get_object_or_404(Collector, id=collector_id)

    # Auto-deactivate expired drives
    all_drives = DonationDrive.objects.filter(collector=collector)
    for drive in all_drives:
        drive.auto_deactivate_if_expired()

    # Send reminder emails for drives in 2 days
    upcoming_drives = DonationDrive.objects.filter(
        collector=collector,
        date=two_days_later,
        is_active=True
    )

    for drive in upcoming_drives:
        appointments = drive.donationappointment_set.all()
        for appointment in appointments:
            donor = appointment.donor
            if donor.email:
                subject = "Reminder: Upcoming Blood Donation Drive for your appointment"
                collector_location = f"{drive.collector.facility_name}, {drive.collector.district}, {drive.collector.province}"
                message = (
                    f"Dear {donor.first_name},\n\n"
                    f"This is a reminder that you have registered to donate blood on {drive.date} at {collector_location}.\n\n"
                    "Please be on time and bring your ID.\n\nThank you for saving lives!"
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [donor.email], fail_silently=True)

    # Show only future active drives (date > today and is_active)
    drives = DonationDrive.objects.filter(
        collector=collector,
        is_active=True,
        date__gt=today
    ).annotate(
        registered_donors=Count('donationappointment')
    ).order_by('date')

    # Use DonationAppointment data for analytics instead of Donor fields

    donors_this_month = DonationAppointment.objects.filter(
        appointment_date__gte=start_of_month
    ).values('donor').distinct().count()

    units_this_week = DonationAppointment.objects.filter(
        appointment_date__gte=start_of_week
    ).count()

    # Monthly donation trend (past ~5 months) from DonationAppointment table
    from_date = today.replace(day=1) - timedelta(days=150)
    monthly_data = DonationAppointment.objects.filter(
        appointment_date__gte=from_date
    ).annotate(
        month=TruncMonth('appointment_date')
    ).values('month').annotate(total=Count('id')).order_by('month')

    donation_trends = [{'month': entry['month'].strftime('%b'), 'count': entry['total']} for entry in monthly_data]

    # ML predictions by blood type using donor.appointments data
    blood_type_predictions = []
    blood_types = Donor.BLOOD_TYPE_CHOICES

    for blood_type, _ in blood_types:
        donors = Donor.objects.filter(blood_type=blood_type)
        probs = []

        for d in donors:
            last = d.appointments.aggregate(max_date=Max('appointment_date'))['max_date']
            first = d.appointments.aggregate(min_date=Min('appointment_date'))['min_date']
            num = d.appointments.count()

            if last:
                months_last = months_since(last)
                months_first = months_since(first or last)
                prob = predict_donation(months_last, num, months_first)
                probs.append(prob)

        if probs:
            avg_prob = np.mean(probs)
            blood_type_predictions.append({
                'type': blood_type,
                'trend': round((avg_prob - 0.5) * 100)  # relative to baseline 50%
            })

    blood_prediction_result = {pred['type']: pred['trend'] for pred in blood_type_predictions}
    month_labels = [entry['month'] for entry in donation_trends]
    donation_chart_data = [entry['count'] for entry in donation_trends]

    # Current blood inventory counts from DonationAppointment table (distinct donors per blood type)
    blood_inventory = {}
    for blood_type, _ in blood_types:
        recent_count = DonationAppointment.objects.filter(
            donor__blood_type=blood_type,
            appointment_date__isnull=False
        ).values('donor').distinct().count()
        blood_inventory[blood_type] = recent_count

    recent_donors = Donor.objects.filter(appointments__appointment_date__isnull=False).order_by('-appointments__appointment_date').distinct()[:5]

    initials = ''.join([name[0] for name in collector.contact_person.split()[:2]]).upper() if collector.contact_person else ''
    full_name = f"{collector.contact_person}" if collector.contact_person else ''
    user_role = "RBC Collector"

    zipped_donation_data = zip(month_labels, donation_chart_data)

    context = {
        'donors_this_month': donors_this_month,
        'units_this_week': units_this_week,
        'blood_inventory': blood_inventory,
        'recent_donors': recent_donors,
        'donation_drives': drives,
        'collector_initials': initials,
        'collector_name': full_name,
        'collector_role': user_role,
        'month_labels': month_labels,
        'donation_trends': donation_trends,
        'blood_type_predictions': blood_type_predictions,
        'blood_prediction_result': blood_prediction_result,
        'donation_chart_data': donation_chart_data,
        'zipped_donation_data': zipped_donation_data,
    }


    return render(request, 'collector.html', context)

#=========================================end of collector view ==============================================

# =========================================donation drive view=================================================

def schedule_drive(request):
    collector_id = request.session.get('collector_id')

    # If not logged in, redirect to collector login page
    if not collector_id:
        messages.error(request, "You must be logged in to schedule a drive.")
        return redirect('collector_login')

    collector = get_object_or_404(Collector, id=collector_id)

    if request.method == 'POST':
        form = DonationDriveForm(request.POST)
        if form.is_valid():
            drive = form.save(commit=False)
            drive.collector = collector
            drive.location = collector.facility_name  # auto-fill location
            drive.save()

            messages.success(request, "✅ Donation drive scheduled successfully!")
            return redirect('collector')  # Redirect to collector dashboard
    else:
        form = DonationDriveForm()

    return render(request, 'schedule_drive.html', {'form': form})

# @login_required
def edit_drive(request, drive_id):
    collector_id = request.session.get('collector_id')
    collector = get_object_or_404(Collector, id=collector_id)

    drive = get_object_or_404(DonationDrive, id=drive_id, collector=collector)

    if request.method == 'POST':
        form = DonationDriveForm(request.POST, instance=drive)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Drive updated successfully.")
            return redirect('collector')
    else:
        form = DonationDriveForm(instance=drive)

    return render(request, 'edit_drive.html', {'form': form, 'drive': drive})


#==========================================message donors on particular donor drive============================
from django.core.mail import send_mass_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mass_mail
from .models import DonationDrive, DonationAppointment

def send_drive_message(request, drive_id):
    drive = get_object_or_404(DonationDrive, id=drive_id)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        body = request.POST.get('body')

        # Get all donor emails registered for this drive
        appointments = DonationAppointment.objects.filter(drive=drive).select_related('donor')
        recipient_emails = [appt.donor.email for appt in appointments if appt.donor.email]

        if recipient_emails:
            # Prepare the message list for each recipient
            messages_to_send = [
                (subject, body, 'noreply@bloodportal.com', [email])
                for email in recipient_emails
            ]
            # Send emails
            send_mass_mail(messages_to_send, fail_silently=False)
            messages.success(request, "✅ Message sent to all registered donors.")
        else:
            messages.warning(request, "⚠️ No donors with email addresses found for this drive.")

        return redirect('collector')  # or wherever you want to go after sending

    # GET request: Show the form
    return render(request, 'send_message_form.html', {
        'drive': drive
    })
#======================================end of messages=======================================================

#========================================delete drive========================================================
# @login_required
def delete_drive(request, drive_id):
    collector_id = request.session.get('collector_id')
    collector = get_object_or_404(Collector, id=collector_id)

    drive = get_object_or_404(DonationDrive, id=drive_id, collector=collector)
    drive.delete()
    messages.success(request, "❌ Drive deleted successfully.")
    return redirect('collector')
#========================================end of delete drive=================================================
#==================================collector password reset request view=====================================
def collector_password_reset_request(request):
    return render(request, 'logincolle.html')


from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .models import Collector

from django.contrib import messages

def collector_reset_password(request, uidb64, token):
    token_generator = PasswordResetTokenGenerator()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        collector = Collector.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Collector.DoesNotExist):
        collector = None

    if collector is not None and token_generator.check_token(collector, token):
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
            elif not username:
                messages.error(request, "Username is required.")
            elif Collector.objects.filter(username=username).exclude(pk=collector.pk).exists():
                messages.error(request, "This username is already taken.")
            else:
                collector.username = username
                collector.password = make_password(password)
                collector.save()
                request.session['collector_id'] = collector.id
                messages.success(request, "Account has been set up and you are now logged in.")
                return redirect('collector')
        return render(request, 'collector_reset_password.html', {'validlink': True, 'collector': collector})
    else:
        return render(request, 'collector_reset_password.html', {'validlink': False})

#==================================end of collector view========================================================

def Profile(request):
    return render(request, 'Profile.html')

# def settings(request):
#     return render(request, 'settings.html')

#==================================donor settings view========================================================
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from .models import Donor  # adjust this if needed
from django.contrib.auth import update_session_auth_hash

def settings(request):
    if not request.session.get('donor_id'):
        return redirect('donor_login')  # Adjust to your login URL name

    donor_id = request.session['donor_id']
    donor = Donor.objects.get(id=donor_id)

    if request.method == 'POST':
        # Update profile info
        donor.first_name = request.POST.get('first_name')
        donor.last_name = request.POST.get('last_name')
        donor.email = request.POST.get('email')
        donor.phone = request.POST.get('phone')
        donor.save()

        # Handle password change
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if current and new and confirm:
            if not check_password(current, donor.password):
                messages.error(request, 'Current password is incorrect.')
            elif new != confirm:
                messages.error(request, 'New passwords do not match.')
            else:
                donor.set_password(new)  # this hashes the password
                donor.save()
                update_session_auth_hash(request, donor)  # Keeps user logged in
                messages.success(request, 'Password updated successfully.')

        return redirect('settings')  # reload page to avoid resubmission

    return render(request, 'settings.html', {'donor': donor})

#==================================end of donor settings view========================================================

# def settingscolle(request):
#     return render(request, 'settingscolle.html')
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Collector

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Collector

from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

def settingscolle(request):
    if 'collector_id' not in request.session:
        return redirect('collector_login')

    try:
        collector = Collector.objects.get(id=request.session['collector_id'])
    except Collector.DoesNotExist:
        messages.error(request, "Collector not found.")
        return redirect('collector_login')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # === Update Profile ===
        if form_type == 'profile':
            collector.contact_person = request.POST.get('contact_person')
            collector.email = request.POST.get('email')
            collector.phone = request.POST.get('phone')
            collector.position = request.POST.get('position')
            collector.save()
            messages.success(request, "Profile updated successfully!")

        # === Update Password ===
        elif form_type == 'password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not check_password(current_password, collector.password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters.')
            else:
                collector.password = make_password(new_password)
                collector.save()
                messages.success(request, 'Password updated successfully!')

    return render(request, 'settingscolle.html', {'collector': collector})

#==================================mass emails notfication view==============================================

# @login_required
def send_mass_notification(request):
    if request.method == 'POST':
        form = MassNotificationForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            blood_type = form.cleaned_data['blood_type']

            # Filter donors
            if blood_type:
                donors = Donor.objects.filter(blood_type=blood_type)
            else:
                donors = Donor.objects.all()

            # Build email list
            emails = [
                (subject, message, 'your_email@example.com', [donor.email])
                for donor in donors if donor.email
            ]

            if emails:
                send_mass_mail(emails, fail_silently=False)

            return render(request, 'notification_success.html')
    else:
        form = MassNotificationForm()

    return render(request, 'send_notification.html', {'form': form})
#==================================end of mass emails notfication view=======================================

def get_drives_by_location(request):
    lat = float(request.GET.get('lat'))
    lon = float(request.GET.get('lon'))

    nearest_collector = None
    min_distance = float('inf')

    for collector in Collector.objects.exclude(location_coordinates__isnull=True).exclude(location_coordinates=''):
        try:
            col_lat, col_lon = map(float, collector.location_coordinates.split(','))
            distance = haversine(lon, lat, col_lon, col_lat)
            if distance < min_distance:
                min_distance = distance
                nearest_collector = collector
        except:
            continue

    drives = DonationDrive.objects.filter(collector=nearest_collector, is_active=True)
    drive_data = [{
        'id': d.id,
        'facility_name': d.collector.facility_name,
        'date': d.date.strftime('%Y-%m-%d')
    } for d in drives]

    return JsonResponse({'drives': drive_data})

#===========================================donor logout=====================
from django.shortcuts import redirect

def donor_logout(request):
    request.session.flush()
    response = redirect('donor_login')
    response.delete_cookie('donor_sessionid')
    return response

#=================================collector logout ====================================================
def collector_logout(request):
    request.session.flush()
    response = redirect('collector_login')
    response.delete_cookie('collector_sessionid')  # ensure it's gone
    return response

#=========================report view ==========================================
# views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils.timezone import now
from django.shortcuts import render, get_object_or_404
from .models import Donor, DonationAppointment, Collector

def generate_reports(request):
    collector_id = request.session.get('collector_id')
    if not collector_id:
        return redirect('collector_login')

    collector = get_object_or_404(Collector, id=collector_id)

    # Report data
    total_donations = DonationAppointment.objects.filter(collector=collector).count()
    donors = Donor.objects.filter(appointments__collector=collector).distinct()
    donation_counts = (
        DonationAppointment.objects.filter(collector=collector)
        .values('donor__blood_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    context = {
        'collector': collector,
        'total_donations': total_donations,
        'donor_list': donors,
        'donation_counts': donation_counts,
    }
    return render(request, 'report.html', context)
