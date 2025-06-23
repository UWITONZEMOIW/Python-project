from django.urls import path
from . import views

urlpatterns = [
    # Homepage and role selection
    path('', views.index, name='index'),
    path('role/', views.role_selection, name='role_selection'),

    # Collector authentication and registration
    
    path('register_collector/', views.register_collector, name='register_collector'),
    #collector reset password
    path('collector/reset/<uidb64>/<token>/', views.collector_reset_password, name='collector_reset_password'),
    path('change-password/', views.change_password, name='change_password'),
    path('collector_login/', views.collector_login, name='collector_login'), 


    # Donor registration 3-step flow
    path('register_donor/', views.register_donor, name='register_donor'),  # Step 1
    path('credential/', views.credential, name='credential'),  # Step 2
    path('complete/', views.complete, name='complete'),  # Step 3
    # Donor login
    path('donor_login/', views.donor_login, name='donor_login'),
    # Dashboard/profile pages
    path('donor/', views.donor, name='donor'),
    #schedule appointment
    path('schedule_appointment/', views.schedule_appointment, name='schedule_appointment'),
    path('collector/', views.collector, name='collector'),
    path('schedule-drive/', views.schedule_drive, name='schedule_drive'),
    path('collector/send-notification/', views.send_mass_notification, name='send_notification'),
    path('collector/schedule-drive/', views.schedule_drive, name='schedule_drive'),
    path('collector/edit-drive/<int:drive_id>/', views.edit_drive, name='edit_drive'),
    path('collector/delete-drive/<int:drive_id>/', views.delete_drive, name='delete_drive'),
    path('get-drives/', views.get_drives_by_location, name='get_drives_by_location'),
    path('drive/<int:drive_id>/message/', views.send_drive_message, name='send_drive_message'),


    # path('send-notification/', views.send_mass_notification, name='send_notification'),
    path('Profile/', views.Profile, name='Profile'),

    # Settings pages
    path('settings_donor/', views.settings, name='settings'),
    path('settings_collector/', views.settingscolle, name='settingscolle'),

    # Password reset endpoints
    path('reset_donor_password/', views.donor_password_reset_request, name='donor_password_reset_request'),
    path('reset_collector_password/', views.collector_password_reset_request, name='collector_password_reset_request'),
   
    # ========================================logout as for donor and collector============================
    path('donor/logout/', views.donor_logout, name='donor_logout'),
    path('collector/logout/', views.collector_logout, name='collector_logout'),

    #==================================report for collector dashboard=======================================
    path('collector/reports/', views.generate_reports, name='generate_reports'),
]


