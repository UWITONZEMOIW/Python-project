from .models import UrgencyBanner

def urgency_banner(request):
    banner = UrgencyBanner.objects.filter(active=True).first()
    return {'urgency_banner': banner}

from bload_donor_app.models import Donor

def donor_counter_number(request):
    total = Donor.objects.count()
    return {'donor_counter_number': total}


