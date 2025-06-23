from django import forms
from .models import *

class DonationDriveForm(forms.ModelForm):
    class Meta:
        model = DonationDrive
        fields = ['date', 'time']  # exclude 'location' — it will be set in the view
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'date': 'Drive Date',
            'time': 'Drive Time',
        }

#================forms for the sending of emails to filtered donors about donation drives and other events==========

from django import forms
from .models import Donor  # Make sure Donor model is imported

class MassNotificationForm(forms.Form):
    subject = forms.CharField(max_length=100, label="Notification Title")
    message = forms.CharField(widget=forms.Textarea, label="Message Content")
    blood_type = forms.ChoiceField(
        choices=[('', 'All')] + list(Donor.BLOOD_TYPE_CHOICES),
        required=False,
        label="Target Blood Type"
    )

