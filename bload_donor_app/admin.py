from django.contrib import admin
from .models import Donor
from .models import Collector,DonationAppointment

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'username', 'dob')
    search_fields = ('first_name', 'last_name', 'username')
    ordering = ('-dob',)

from django.contrib import admin
from .models import Collector, DonationAppointment
from django.contrib.auth.hashers import make_password

@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    list_display = ('facility_name', 'facility_type', 'district', 'phone', 'email')
    ordering = ['district']  # Ascending order by district

    def save_model(self, request, obj, form, change):
        send_reset = False

        if change:
            try:
                old = Collector.objects.get(pk=obj.pk)
                if not old.password and obj.password and obj.username:
                    send_reset = True
            except Collector.DoesNotExist:
                pass

        # Hash the password if it's not already hashed
        if obj.password and not obj.password.startswith('pbkdf2_'):
            obj.password = make_password(obj.password)

        super().save_model(request, obj, form, change)

        if send_reset:
            obj.send_password_reset_email()

@admin.register(DonationAppointment)
class DonationAppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'get_donor_full_name',
        'appointment_date',
        'appointment_time',
        'selected_center',
        'donor_coordinates',
        'collector_coordinates',
        'confirmed',
    )

    @admin.display(description='Donor')
    def get_donor_full_name(self, obj):
        return obj.donor.full_name if obj.donor else "-"

from .models import (
    Testimonial,
    FAQ,
    ProgressTracker,
    UrgencyBanner,
    DonationDrive,
)
admin.site.register(Testimonial)
admin.site.register(FAQ)
admin.site.register(ProgressTracker)
admin.site.register(UrgencyBanner)
admin.site.register(DonationDrive)

