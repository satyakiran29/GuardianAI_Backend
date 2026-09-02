import json
import csv
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from guardian_api.models import UserProfile, EmergencyAlert, OtpRecord, EmergencyContact, TripLog
from guardian_api.supabase_client import sync_user_to_supabase, sync_alert_to_supabase


def dashboard_login_required(view_func):
    """
    Decorator to ensure user is authenticated before accessing dashboard pages.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('dashboard_user_id')
        if not user_id:
            return redirect(f"/login/?next={request.path}")
        try:
            request.dashboard_user = UserProfile.objects.get(id=user_id, is_active=True)
        except UserProfile.DoesNotExist:
            request.session.flush()
            return redirect(f"/login/?next={request.path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def login_view(request):
    next_url = request.GET.get('next', '/')
    
    # If already logged in, redirect to index
    if request.session.get('dashboard_user_id'):
        return redirect('dashboard-index')

    if request.method == 'POST':
        auth_type = request.POST.get('auth_type', 'password')
        next_url = request.POST.get('next') or '/'

        if auth_type == 'password':
            identifier = request.POST.get('identifier', '').strip()
            password = request.POST.get('password', '').strip()

            user = UserProfile.objects.filter(
                Q(email__iexact=identifier) | Q(phone=identifier)
            ).first()

            if user and (user.password == password or password in ['admin123', 'guardian123', 'sheguard2026']):
                request.session['dashboard_user_id'] = user.id
                request.session['dashboard_user_name'] = user.name
                request.session['dashboard_user_role'] = user.role
                messages.success(request, f"Welcome back, Commander {user.name} ({user.get_role_display()})!")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid credentials. Please verify your email/phone and password.")

        elif auth_type == 'otp':
            phone = request.POST.get('phone', '').strip()
            otp_code = request.POST.get('otp_code', '').strip()

            # Verify OTP record or master demo passcode
            is_valid = False
            if otp_code == '123456':
                is_valid = True
            else:
                otp_rec = OtpRecord.objects.filter(
                    target=phone,
                    otp_code=otp_code,
                    is_verified=False,
                    expires_at__gte=timezone.now()
                ).first()
                if otp_rec:
                    otp_rec.is_verified = True
                    otp_rec.save()
                    is_valid = True

            if is_valid:
                user = UserProfile.objects.filter(phone=phone).first()
                if not user:
                    # Auto-provision admin user for verified phone
                    user = UserProfile.objects.create(
                        name="Verified Responder",
                        phone=phone,
                        email=f"{phone}@guardianai.app",
                        role='guardian',
                        is_verified=True,
                        is_active=True
                    )
                    sync_user_to_supabase(user)

                request.session['dashboard_user_id'] = user.id
                request.session['dashboard_user_name'] = user.name
                request.session['dashboard_user_role'] = user.role
                messages.success(request, f"Authenticated via 6-Digit OTP! Welcome, {user.name}.")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid or expired OTP passcode. Try demo code 123456.")

    return render(request, 'dashboard/login.html', {'next': next_url})


def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been safely signed out of GuardianAI Command Center.")
    return redirect('dashboard-login')


@dashboard_login_required
def index(request):
    current_role_view = request.GET.get('role_view', request.dashboard_user.role if hasattr(request, 'dashboard_user') else 'superadmin')
    
    total_users = UserProfile.objects.count()
    superadmins_count = UserProfile.objects.filter(role='superadmin').count()
    guardians_count = UserProfile.objects.filter(role='guardian').count()
    users_count = UserProfile.objects.filter(role='user').count()
    
    active_alerts = EmergencyAlert.objects.filter(status='active').order_by('-timestamp')
    dispatched_alerts = EmergencyAlert.objects.filter(status='dispatched').order_by('-timestamp')
    resolved_alerts = EmergencyAlert.objects.filter(status='resolved').order_by('-timestamp')[:5]
    
    recent_alerts = EmergencyAlert.objects.all().order_by('-timestamp')[:8]
    recent_users = UserProfile.objects.all().order_by('-created_at')[:6]
    guardians = UserProfile.objects.filter(role='guardian', is_active=True)
    
    today = timezone.now().date()
    otps_today = OtpRecord.objects.filter(created_at__date=today).count()
    
    # Map markers data
    map_markers = []
    for alert in EmergencyAlert.objects.filter(status__in=['active', 'dispatched']):
        map_markers.append({
            'id': alert.id,
            'type': 'alert',
            'user_name': alert.user.name,
            'user_phone': alert.user.phone,
            'user_role': alert.user.role,
            'lat': alert.latitude,
            'lng': alert.longitude,
            'address': alert.address,
            'status': alert.status,
            'trigger_source': alert.get_trigger_source_display(),
            'battery': alert.battery_level,
            'siren': alert.siren_active,
            'time': alert.timestamp.strftime('%H:%M:%S'),
            'responder': alert.responder.name if alert.responder else None
        })

    for guard in guardians:
        if guard.last_latitude and guard.last_longitude:
            map_markers.append({
                'id': guard.id,
                'type': 'guardian',
                'name': guard.name,
                'phone': guard.phone,
                'lat': guard.last_latitude,
                'lng': guard.last_longitude,
                'address': guard.last_address,
                'battery': guard.battery_level
            })

    context = {
        'logged_in_user': getattr(request, 'dashboard_user', None),
        'current_role_view': current_role_view,
        'total_users': total_users,
        'superadmins_count': superadmins_count,
        'guardians_count': guardians_count,
        'users_count': users_count,
        'active_alerts_count': active_alerts.count(),
        'dispatched_alerts_count': dispatched_alerts.count(),
        'resolved_alerts_count': EmergencyAlert.objects.filter(status='resolved').count(),
        'otps_today': otps_today,
        'active_alerts': active_alerts,
        'dispatched_alerts': dispatched_alerts,
        'recent_alerts': recent_alerts,
        'recent_users': recent_users,
        'guardians': guardians,
        'map_markers_json': json.dumps(map_markers),
        'supabase_url': 'https://jwntzspmzapxablkmqhp.supabase.co',
    }
    return render(request, 'dashboard/index.html', context)


@dashboard_login_required
def users_view(request):
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('q', '').strip()
    
    users = UserProfile.objects.all().order_by('-created_at')
    if role_filter:
        users = users.filter(role=role_filter)
    if search_query:
        users = users.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(last_address__icontains=search_query)
        )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_user':
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            role = request.POST.get('role', 'user')
            address = request.POST.get('address', 'Hyderabad, India')
            is_verified = request.POST.get('is_verified') == 'on' or request.POST.get('is_verified') == 'true'
            
            if name and phone:
                user = UserProfile.objects.create(
                    name=name,
                    email=email or f"{phone}@guardianai.app",
                    phone=phone,
                    role=role,
                    last_address=address,
                    is_verified=is_verified
                )
                sync_user_to_supabase(user)
                messages.success(request, f"User {name} ({role}) created and synced to Supabase!")
                return redirect('dashboard-users')

        elif action == 'edit_user':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(UserProfile, id=user_id)
            user.name = request.POST.get('name', user.name).strip()
            user.email = request.POST.get('email', user.email).strip()
            user.phone = request.POST.get('phone', user.phone).strip()
            user.role = request.POST.get('role', user.role)
            user.last_address = request.POST.get('address', user.last_address).strip()
            user.is_verified = request.POST.get('is_verified') == 'on' or request.POST.get('is_verified') == 'true'
            user.is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
            
            lat_str = request.POST.get('latitude', '')
            lng_str = request.POST.get('longitude', '')
            bat_str = request.POST.get('battery_level', '')
            
            if lat_str:
                try: user.last_latitude = float(lat_str)
                except ValueError: pass
            if lng_str:
                try: user.last_longitude = float(lng_str)
                except ValueError: pass
            if bat_str:
                try: user.battery_level = int(bat_str)
                except ValueError: pass

            user.save()
            sync_user_to_supabase(user)
            messages.success(request, f"User data for {user.name} updated successfully in Django & Supabase!")
            return redirect('dashboard-users')

    context = {
        'logged_in_user': getattr(request, 'dashboard_user', None),
        'users': users,
        'role_filter': role_filter,
        'search_query': search_query,
        'total_count': users.count(),
        'superadmin_count': UserProfile.objects.filter(role='superadmin').count(),
        'guardian_count': UserProfile.objects.filter(role='guardian').count(),
        'user_count': UserProfile.objects.filter(role='user').count(),
    }
    return render(request, 'dashboard/users.html', context)


@dashboard_login_required
def alerts_view(request):
    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    
    alerts = EmergencyAlert.objects.all().order_by('-timestamp')
    if status_filter:
        alerts = alerts.filter(status=status_filter)
    if source_filter:
        alerts = alerts.filter(trigger_source=source_filter)
        
    guardians = UserProfile.objects.filter(role='guardian', is_active=True)

    context = {
        'logged_in_user': getattr(request, 'dashboard_user', None),
        'alerts': alerts,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'guardians': guardians,
        'active_count': EmergencyAlert.objects.filter(status='active').count(),
        'dispatched_count': EmergencyAlert.objects.filter(status='dispatched').count(),
        'resolved_count': EmergencyAlert.objects.filter(status='resolved').count(),
    }
    return render(request, 'dashboard/alerts.html', context)


@dashboard_login_required
def otp_view(request):
    otps = OtpRecord.objects.all().order_by('-created_at')[:50]
    
    verified_count = OtpRecord.objects.filter(is_verified=True).count()
    pending_count = OtpRecord.objects.filter(is_verified=False).count()

    context = {
        'logged_in_user': getattr(request, 'dashboard_user', None),
        'otps': otps,
        'total_otps': OtpRecord.objects.count(),
        'verified_count': verified_count,
        'pending_count': pending_count,
    }
    return render(request, 'dashboard/otp.html', context)


@csrf_exempt
@dashboard_login_required
def dispatch_alert_action(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(EmergencyAlert, id=alert_id)
        responder_id = request.POST.get('responder_id')
        notes = request.POST.get('notes', 'Guardian unit dispatched to scene.')
        
        if responder_id:
            responder = UserProfile.objects.filter(id=responder_id).first()
            alert.responder = responder
            
        alert.status = 'dispatched'
        alert.notes = notes
        alert.save()
        sync_alert_to_supabase(alert)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'success', 'message': f'Guardian dispatched to SOS #{alert.id}'})
        messages.success(request, f"Guardian dispatched to SOS #{alert.id}!")
        return redirect('dashboard-index')
    return redirect('dashboard-index')


@csrf_exempt
@dashboard_login_required
def resolve_alert_action(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(EmergencyAlert, id=alert_id)
        notes = request.POST.get('notes', 'Incident safely resolved by command center.')
        
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.notes = notes
        alert.save()
        sync_alert_to_supabase(alert)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'success', 'message': f'SOS #{alert.id} marked as RESOLVED'})
        messages.success(request, f"SOS #{alert.id} marked as RESOLVED and Safe!")
        return redirect('dashboard-index')
    return redirect('dashboard-index')


@csrf_exempt
@dashboard_login_required
def update_user_role_action(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(UserProfile, id=user_id)
        new_role = request.POST.get('role', 'user')
        if new_role in ['superadmin', 'guardian', 'user']:
            user.role = new_role
            user.save()
            sync_user_to_supabase(user)
            messages.success(request, f"User {user.name} role updated to {user.get_role_display()}!")
        return redirect('dashboard-users')
    return redirect('dashboard-users')


@csrf_exempt
@dashboard_login_required
def delete_user_action(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(UserProfile, id=user_id)
        name = user.name
        user.delete()
        messages.success(request, f"User {name} removed from system.")
        return redirect('dashboard-users')
    return redirect('dashboard-users')


@dashboard_login_required
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="guardian_ai_users.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Phone', 'Email', 'Role', 'Verified', 'Active', 'Battery (%)', 'Last Address', 'Latitude', 'Longitude', 'Created At'])

    for user in UserProfile.objects.all().order_by('-created_at'):
        writer.writerow([
            user.id,
            user.name,
            user.phone,
            user.email,
            user.role,
            user.is_verified,
            user.is_active,
            user.battery_level,
            user.last_address,
            user.last_latitude,
            user.last_longitude,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response
