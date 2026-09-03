from django.db import models
from django.utils import timezone
import datetime

ROLE_CHOICES = [
    ('superadmin', 'Super Admin'),
    ('guardian', 'Guardian / Responder'),
    ('user', 'Protected User'),
]

ALERT_STATUS_CHOICES = [
    ('active', 'Active Emergency'),
    ('dispatched', 'Guardian Dispatched'),
    ('resolved', 'Resolved / Safe'),
]

TRIGGER_SOURCE_CHOICES = [
    ('button', 'SOS Button'),
    ('shake', 'Shake Gesture'),
    ('voice', 'Voice Keyword'),
    ('timer', 'Safety Timer Expired'),
    ('battery', 'Low Battery (15%) Alert'),
    ('safe_mode', 'Safe Mode Broadcast'),
    ('trip', 'Trip Off-Route Divergence'),
]

class UserProfile(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=255, default='guardian123')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Telemetry / Live Status
    last_latitude = models.FloatField(null=True, blank=True, default=17.3850)
    last_longitude = models.FloatField(null=True, blank=True, default=78.4867)
    last_address = models.CharField(max_length=255, blank=True, default='Hyderabad, Telangana')
    battery_level = models.IntegerField(default=85)
    fcm_token = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) - {self.phone}"


class EmergencyAlert(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='alerts')
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255, blank=True, default='Live Location')
    trigger_source = models.CharField(max_length=30, choices=TRIGGER_SOURCE_CHOICES, default='button')
    status = models.CharField(max_length=20, choices=ALERT_STATUS_CHOICES, default='active')
    siren_active = models.BooleanField(default=True)
    battery_level = models.IntegerField(default=100)
    responder = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_alerts')
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"SOS #{self.id} - {self.user.name} ({self.status})"


class OtpRecord(models.Model):
    target = models.CharField(max_length=100) # Phone number or Email
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, default='registration') # registration, login, reset, sos
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP {self.otp_code} for {self.target} ({'Verified' if self.is_verified else 'Pending'})"


class EmergencyContact(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50, default='Family')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.relationship}) -> {self.user.name}"


class TripLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='trips')
    vehicle_number = models.CharField(max_length=50)
    driver_name = models.CharField(max_length=100, blank=True)
    destination = models.CharField(max_length=255)
    status = models.CharField(max_length=30, default='active') # active, completed, alert
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Trip {self.vehicle_number} - {self.user.name}"


class GuardianLink(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='guardian_links')
    guardian = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ward_links')
    relationship = models.CharField(max_length=50, default='Family')
    status = models.CharField(max_length=20, default='active') # active, pending, revoked
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'guardian')

    def __str__(self):
        return f"{self.guardian.name} (Guardian) -> {self.user.name} (Protected User) [{self.relationship}]"


class ChatMessage(models.Model):
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_sos = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    battery_level = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M')}] {self.sender.name} -> {self.receiver.name}: {self.message[:30]}"
