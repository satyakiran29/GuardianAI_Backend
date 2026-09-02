from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from guardian_api.models import UserProfile, EmergencyAlert, OtpRecord, EmergencyContact, TripLog
from guardian_api.supabase_client import sync_user_to_supabase, sync_alert_to_supabase

class Command(BaseCommand):
    help = 'Seed database with SuperAdmin, Guardian Responders, Users, SOS Alerts, and OTP Logs'

    def handle(self, *args, **options):
        self.stdout.write("Seeding GuardianAI database with multi-role system...")

        # 1. SuperAdmins
        superadmin, _ = UserProfile.objects.update_or_create(
            phone="+919999000001",
            defaults={
                'name': 'Pampana Satya Kiran',
                'email': 'satya@guardianai.app',
                'password': 'admin123',
                'role': 'superadmin',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.385044,
                'last_longitude': 78.486671,
                'last_address': 'Guardian HQ Command Center, Hyderabad',
                'battery_level': 100
            }
        )

        superadmin2, _ = UserProfile.objects.update_or_create(
            phone="+919999000099",
            defaults={
                'name': 'System Administrator',
                'email': 'superadmin@guardianai.app',
                'password': 'admin123',
                'role': 'superadmin',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.4435,
                'last_longitude': 78.3772,
                'last_address': 'HITEC City Central Server Hub, Hyderabad',
                'battery_level': 98
            }
        )

        # 2. Guardians / Responders
        guardian_mom, _ = UserProfile.objects.update_or_create(
            phone="+15552345678",
            defaults={
                'name': 'Mom (Primary Guardian)',
                'email': 'mom@guardianai.app',
                'password': 'guardian123',
                'role': 'guardian',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.4123,
                'last_longitude': 78.4080,
                'last_address': 'Banjara Hills Safe Zone, Hyderabad',
                'battery_level': 92
            }
        )

        guardian_security, _ = UserProfile.objects.update_or_create(
            phone="+919999000002",
            defaults={
                'name': 'Campus Quick Response Escort',
                'email': 'campus.guard@guardianai.app',
                'password': 'guardian123',
                'role': 'guardian',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.3980,
                'last_longitude': 78.4900,
                'last_address': 'University Security Patrol Station',
                'battery_level': 88
            }
        )

        guardian_police, _ = UserProfile.objects.update_or_create(
            phone="+919999000003",
            defaults={
                'name': 'Inspector Sneha Reddy (SHE Team)',
                'email': 'sheteam.hyd@telangana.gov.in',
                'password': 'guardian123',
                'role': 'guardian',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.4065,
                'last_longitude': 78.4772,
                'last_address': 'SHE Team Women Safety Division',
                'battery_level': 95
            }
        )

        # 3. Protected Users
        demo_user, _ = UserProfile.objects.update_or_create(
            phone="+15551234567",
            defaults={
                'name': 'Jane Doe (Demo User)',
                'email': 'demo@guardianai.app',
                'password': 'demo123',
                'role': 'user',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.4399,
                'last_longitude': 78.3812,
                'last_address': 'Cyber Towers Junction, Madhapur',
                'battery_level': 74
            }
        )

        user_priya, _ = UserProfile.objects.update_or_create(
            phone="+919876501234",
            defaults={
                'name': 'Priya Sharma',
                'email': 'priya.sharma@example.com',
                'password': 'user123',
                'role': 'user',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.4250,
                'last_longitude': 78.4520,
                'last_address': 'Somajiguda Metro Station, Hyderabad',
                'battery_level': 14  # Low battery example!
            }
        )

        user_ananya, _ = UserProfile.objects.update_or_create(
            phone="+919876505678",
            defaults={
                'name': 'Ananya Verma',
                'email': 'ananya.v@example.com',
                'password': 'user123',
                'role': 'user',
                'is_verified': True,
                'is_active': True,
                'last_latitude': 17.3616,
                'last_longitude': 78.4747,
                'last_address': 'Charminar Heritage Route',
                'battery_level': 65
            }
        )

        # 4. Emergency Contacts for Users
        EmergencyContact.objects.get_or_create(
            user=demo_user,
            phone="+15552345678",
            defaults={'name': 'Mom', 'relationship': 'Parent', 'is_primary': True}
        )
        EmergencyContact.objects.get_or_create(
            user=demo_user,
            phone="+15558765432",
            defaults={'name': 'Alex (Roommate)', 'relationship': 'Friend', 'is_primary': False}
        )
        EmergencyContact.objects.get_or_create(
            user=demo_user,
            phone="+15559990000",
            defaults={'name': 'Campus Security Control', 'relationship': 'Authority', 'is_primary': False}
        )

        EmergencyContact.objects.get_or_create(
            user=user_priya,
            phone="+919999000003",
            defaults={'name': 'SHE Team Helpline', 'relationship': 'Police Patrol', 'is_primary': True}
        )

        # 5. Realistic Emergency Alerts
        # Alert 1: Active Alert (Priya - Low battery + Shake SOS)
        alert1, _ = EmergencyAlert.objects.get_or_create(
            user=user_priya,
            status='active',
            defaults={
                'latitude': 17.4250,
                'longitude': 78.4520,
                'address': 'Somajiguda Metro Pillar 1042, Hyderabad',
                'trigger_source': 'shake',
                'siren_active': True,
                'battery_level': 14,
                'notes': 'High Priority: Low battery (14%) + Shake gesture triggered on commute.'
            }
        )

        # Alert 2: Dispatched Alert (Demo User - Voice Trigger, Guard assigned)
        alert2, _ = EmergencyAlert.objects.get_or_create(
            user=demo_user,
            status='dispatched',
            defaults={
                'latitude': 17.4399,
                'longitude': 78.3812,
                'address': 'Cyber Towers Junction, Madhapur, Hyderabad',
                'trigger_source': 'voice',
                'siren_active': False,
                'battery_level': 74,
                'responder': guardian_security,
                'notes': 'Voice SOS keyword "HELP" detected. Campus Quick Response Escort dispatched.'
            }
        )

        # Alert 3: Resolved Alert (Ananya - Safe Arrival Check-in)
        alert3, _ = EmergencyAlert.objects.get_or_create(
            user=user_ananya,
            status='resolved',
            defaults={
                'latitude': 17.3616,
                'longitude': 78.4747,
                'address': 'Charminar Safe Zone, Old City, Hyderabad',
                'trigger_source': 'button',
                'siren_active': False,
                'battery_level': 82,
                'responder': guardian_police,
                'resolved_at': timezone.now() - datetime.timedelta(hours=2),
                'notes': 'Citizen safely escorted to destination by SHE Team.'
            }
        )

        # 6. Seed Realistic OTP Records
        OtpRecord.objects.get_or_create(
            target="+15551234567",
            otp_code="123456",
            defaults={
                'purpose': 'login',
                'is_verified': True,
                'expires_at': timezone.now() + datetime.timedelta(days=365)
            }
        )

        OtpRecord.objects.get_or_create(
            target="+919876501234",
            otp_code="482910",
            defaults={
                'purpose': 'registration',
                'is_verified': True,
                'expires_at': timezone.now() + datetime.timedelta(minutes=5)
            }
        )

        OtpRecord.objects.get_or_create(
            target="priya.sharma@example.com",
            otp_code="739104",
            defaults={
                'purpose': 'verification',
                'is_verified': True,
                'expires_at': timezone.now() + datetime.timedelta(minutes=8)
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded GuardianAI multi-role data!"))
