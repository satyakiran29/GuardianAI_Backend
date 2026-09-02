"""
Transactional Email Engine for GuardianAI
Dispatches HTML OTP codes and SOS Emergency Alert broadcasts via Gmail SMTP.
"""
import os
import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def _send_email_task(to_email, subject, html_content, from_email=None):
    """
    Background worker function to dispatch transactional emails safely via Gmail SMTP.
    """
    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'GuardianAI Safety <satyakiran294@gmail.com>')
    recipients = [to_email] if isinstance(to_email, str) else to_email

    try:
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipients)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
        logger.info(f"📧 [Gmail SMTP] Email dispatched to {to_email}")
        return True
    except Exception as smtp_err:
        logger.warning(f"⚠️ [Gmail SMTP] Exception while sending to {to_email}: {smtp_err}")
        return False


def send_email_via_resend(to_email, subject, html_content, from_email=None):
    """
    Non-blocking async dispatch of emails to guarantee zero HTTP request latency and zero worker timeouts.
    """
    try:
        t = threading.Thread(
            target=_send_email_task,
            args=(to_email, subject, html_content, from_email),
            daemon=True
        )
        t.start()
        return True
    except Exception as e:
        logger.error(f"❌ Failed to spawn email thread: {e}")
        return False


def send_otp_email(to_email, otp_code, purpose="Authentication"):
    """
    Sends a styled OTP verification email via Resend.
    """
    subject = f"🛡️ {otp_code} is your GuardianAI Verification Code"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1120; color: #f8fafc; margin: 0; padding: 24px; }}
        .card {{ max-width: 480px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .logo {{ font-size: 36px; }}
        .title {{ font-size: 22px; font-weight: 700; color: #ffffff; margin: 8px 0 4px; }}
        .subtitle {{ font-size: 14px; color: #94a3b8; }}
        .otp-box {{ background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(236,72,153,0.15)); border: 2px dashed #8b5cf6; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
        .otp-code {{ font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #c084fc; font-family: monospace; margin: 0; }}
        .note {{ font-size: 13px; color: #94a3b8; line-height: 1.5; text-align: center; }}
        .footer {{ margin-top: 28px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #334155; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <div class="logo">🛡️</div>
          <div class="title">GuardianAI Security</div>
          <div class="subtitle">Purpose: {purpose.capitalize()}</div>
        </div>
        <p style="color: #cbd5e1; font-size: 14px;">Please use the following 6-digit passcode to verify your GuardianAI identity. This code is valid for <strong>10 minutes</strong>.</p>
        <div class="otp-box">
          <div class="otp-code">{otp_code}</div>
        </div>
        <p class="note">If you did not request this verification code, please ignore this email or notify your guardian team immediately.</p>
        <div class="footer">
          &copy; 2026 GuardianAI Incident Command System • SheGuard Safety Network
        </div>
      </div>
    </body>
    </html>
    """
    return send_email_via_resend(to_email, subject, html)


def send_sos_alert_email(to_email, user_name, user_phone, address, lat, lng, trigger_source="SOS Button"):
    """
    Sends a high-priority emergency SOS notification email to emergency contacts.
    """
    subject = f"🚨 CRITICAL SOS ALERT: {user_name} needs urgent assistance!"
    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #450a0a; color: #fef2f2; margin: 0; padding: 24px; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #1c1917; border: 2px solid #ef4444; border-radius: 16px; padding: 32px; box-shadow: 0 10px 30px rgba(239,68,68,0.3); }}
        .badge {{ background: #dc2626; color: #fff; display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }}
        .title {{ font-size: 24px; font-weight: 800; color: #fee2e2; margin: 16px 0 8px; }}
        .info-row {{ background: #292524; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; font-size: 14px; }}
        .btn {{ display: block; background: #ef4444; color: #ffffff !important; text-align: center; text-decoration: none; padding: 14px 20px; border-radius: 10px; font-weight: 700; font-size: 16px; margin: 24px 0 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <span class="badge">🚨 Emergency Incident</span>
        <div class="title">SOS Triggered by {user_name}</div>
        <p style="color: #fca5a5; font-size: 14px;">An emergency panic signal has been dispatched through GuardianAI.</p>
        
        <div class="info-row"><strong>👤 Citizen:</strong> {user_name} ({user_phone})</div>
        <div class="info-row"><strong>📍 Location:</strong> {address}</div>
        <div class="info-row"><strong>⚡ Trigger Type:</strong> {trigger_source.capitalize()}</div>
        <div class="info-row"><strong>🌐 Coordinates:</strong> {lat}, {lng}</div>
        
        <a href="{maps_url}" class="btn" target="_blank">📍 Open Live Location in Google Maps</a>
        
        <p style="font-size: 12px; color: #a8a29e; text-align: center;">Please reach out to the citizen or dispatch emergency authorities (112 / Police) immediately.</p>
      </div>
    </body>
    </html>
    """
    return send_email_via_resend(to_email, subject, html)
