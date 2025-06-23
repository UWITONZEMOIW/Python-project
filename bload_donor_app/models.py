# models.py file for tables
from django.db import models
from django.contrib.auth.hashers import make_password,check_password
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.db import models
from django.db.models import Min, Max

#==================================== model for the blood donors==============================================

class Donor(models.Model):
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES)

    # Location
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)

    # Optional/Extra Information
    donation_time = models.CharField(max_length=10)
    additional_info = models.TextField(blank=True)
    has_donated_before = models.BooleanField(default=False)
    last_donation_before_registration = models.DateField(null=True, blank=True)

    # System Credentials
    username = models.CharField(max_length=150, unique=True, null=False, blank=False)
    password = models.CharField(max_length=255, null=True, blank=True)

    # === Dynamic Historical Properties ===

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def first_donation_date(self):
        return self.appointments.aggregate(first=Min('appointment_date'))['first']

    def last_donation_date(self):
        return self.appointments.aggregate(last=Max('appointment_date'))['last']

    def num_donations(self):
        return self.appointments.count()

    def has_ever_donated(self):
        return self.appointments.exists()

    # === Password Handling ===
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.full_name} ({self.blood_type})"

#=================================model for the blood collectors===========================================


from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class Collector(models.Model):
    # Facility Details
    facility_name = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=50)
    license_number = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    location = models.CharField(max_length=200, null=True, blank=True)
    location_coordinates = models.CharField(
        max_length=100,
        help_text="Latitude,Longitude format",
        null=True,
        blank=True
    )

    # Contact
    contact_person = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    # Operating Info
    staff_capacity = models.CharField(max_length=50, null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)
    last_login = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=False)

    # Login Credentials
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Detect activation and if credentials haven't been set
        if self.pk:
            old = Collector.objects.get(pk=self.pk)
            if not old.is_active and self.is_active and not self.username:
                super().save(*args, **kwargs)
                self.send_account_setup_email()
                return

        # Hash password if it's a plain one
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def send_account_setup_email(self):
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self)
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        setup_url = settings.SITE_URL + reverse('collector_reset_password', kwargs={'uidb64': uid, 'token': token})

        subject = "Set Up Your RBC Collector Portal Account"
        message = f"""
Hello {self.contact_person},

Your facility has been registered in the Rwanda Biomedical Center's Blood Collection System.

Please set your username and password by clicking the link below:

{setup_url}

This link will expire soon. If you didn’t request this, please ignore it.

Thank you,
RBC Blood Collection System
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False
        )

    def get_email_field_name(self):
        return 'email'

    def get_username(self):
        return self.username


    def __str__(self):
        return self.facility_name

#================================UrgencyBanner table for being dynamically updated========================== 
class UrgencyBanner(models.Model):
    message = models.TextField()
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.message

#================================================making the dirve table========================================
from datetime import date

class DonationDrive(models.Model):
    collector = models.ForeignKey(Collector, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} at {self.collector.facility_name} on {self.date}"

    def is_expired(self):
        return self.date <= date.today()

    def auto_deactivate_if_expired(self):
        if self.is_expired() and self.is_active:
            self.is_active = False
            self.save()

#=================================== donation appointment=========================================================
class DonationAppointment(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    drive = models.ForeignKey(DonationDrive, on_delete=models.SET_NULL, null=True, blank=True)
    collector = models.ForeignKey(Collector, on_delete=models.SET_NULL, null=True, blank=True)
    selected_center = models.CharField(max_length=255)
    confirmed = models.BooleanField(default=False)
    donor_coordinates = models.CharField(max_length=100, null=True, blank=True)
    collector_coordinates = models.CharField(max_length=100, null=True, blank=True)

    # ✅ New field: Tracks whether this donor had donated *before* this appointment
    has_donated_before = models.BooleanField(default=False)

    def __str__(self):
     return f"{self.donor} on {self.appointment_date} at {self.selected_center}"
    
#================================= end of donation appointment model ======================================


# ====================================Testimonial==========================================================
class Testimonial(models.Model):
    author_name = models.CharField(max_length=100)
    story = models.TextField()
    image_url = models.URLField(blank=True)
    role = models.CharField(max_length=100, help_text="e.g., Cancer Survivor, Grateful Mother")

    def __str__(self):
        return f"{self.author_name} ({self.role})"
    
# Reward Badge
class Reward(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10)  # Emoji or icon name
    donors = models.ManyToManyField(Donor, related_name='rewards', blank=True)

    def __str__(self):
        return self.title

#=================================frequently asked questions table========================================
class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

#=================================Progress Tracker for monthly donation goals=============================
from django.utils import timezone

class ProgressTracker(models.Model):
    month = models.DateField(default=timezone.now)
    target_donations = models.PositiveIntegerField()
    actual_donations = models.PositiveIntegerField(default=0)
    goal_met = models.BooleanField(default=False)

    def update_goal_status(self):
        self.goal_met = self.actual_donations >= self.target_donations
        self.save()

    def __str__(self):
        return f"{self.month.strftime('%B %Y')} Progress"


