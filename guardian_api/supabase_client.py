"""
Supabase Cloud Integration Client for GuardianAI
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        from supabase import create_client
        url = getattr(settings, 'SUPABASE_URL', "https://jwntzspmzapxablkmqhp.supabase.co")
        key = getattr(settings, 'SUPABASE_KEY', "sb_publishable_jB5ChDHJa-XPwBPyoHMLNQ_1kZb3AMv")
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logger.warning(f"Supabase client initialization notice: {e}")
        return None


def sync_user_to_supabase(user_profile):
    """
    Sync user profile data to Supabase database.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        payload = {
            "name": user_profile.name,
            "email": user_profile.email,
            "phone": user_profile.phone,
            "role": user_profile.role,
            "is_verified": user_profile.is_verified,
            "last_latitude": user_profile.last_latitude,
            "last_longitude": user_profile.last_longitude,
            "last_address": user_profile.last_address,
            "battery_level": user_profile.battery_level,
            "updated_at": user_profile.updated_at.isoformat() if hasattr(user_profile, 'updated_at') else None
        }
        # Upsert by phone/email
        res = client.table("guardian_users").upsert(payload, on_conflict="phone").execute()
        return True
    except Exception as e:
        logger.info(f"Supabase user sync notice: {e}")
        return False


def sync_alert_to_supabase(alert):
    """
    Broadcast emergency SOS alert to Supabase real-time table.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        payload = {
            "user_name": alert.user.name,
            "user_phone": alert.user.phone,
            "user_role": alert.user.role,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "address": alert.address,
            "trigger_source": alert.trigger_source,
            "status": alert.status,
            "siren_active": alert.siren_active,
            "battery_level": alert.battery_level,
            "timestamp": alert.timestamp.isoformat() if hasattr(alert, 'timestamp') else None,
        }
        res = client.table("emergency_alerts").insert(payload).execute()
        return True
    except Exception as e:
        logger.info(f"Supabase alert sync notice: {e}")
        return False


def sync_otp_to_supabase(otp_record):
    """
    Sync OTP record to Supabase.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        payload = {
            "target": otp_record.target,
            "otp_code": otp_record.otp_code,
            "purpose": otp_record.purpose,
            "is_verified": otp_record.is_verified,
            "expires_at": otp_record.expires_at.isoformat()
        }
        res = client.table("otp_records").insert(payload).execute()
        return True
    except Exception as e:
        logger.info(f"Supabase OTP sync notice: {e}")
        return False
