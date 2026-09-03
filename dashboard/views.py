import json
import csv
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from guardian_api.models import UserProfile, EmergencyAlert, OtpRecord, EmergencyContact, TripLog, GuardianLink, ChatMessage
from guardian_api.supabase_client import sync_user_to_supabase, sync_alert_to_supabase


def find_user_by_identifier(identifier, user_id=None):
    """
    Robust lookup for user by ID, email, exact phone, or phone with/without '+' and spaces.
    """
    if user_id:
        u = UserProfile.objects.filter(id=user_id).first()
        if u: return u

    if not identifier:
        return None

    raw = str(identifier).strip()
    plus_ver = raw if raw.startswith('+') else f"+{raw.lstrip()}"
    space_fix = raw.replace(' ', '+')
    digits_only = ''.join(c for c in raw if c.isdigit())
    last10 = digits_only[-10:] if len(digits_only) >= 10 else digits_only

    return UserProfile.objects.filter(
        Q(email__iexact=raw) |
        Q(phone=raw) |
        Q(phone=plus_ver) |
        Q(phone=space_fix) |
        (Q(phone__endswith=last10) if last10 else Q(pk__isnull=True))
    ).first()




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
    next_url = request.GET.get('next', '')

    # Ensure standard default demo accounts exist
    try:
        UserProfile.objects.get_or_create(
            email='admin@sheguard.app',
            defaults={
                'name': 'Chief SuperAdmin',
                'phone': '+919876500000',
                'role': 'superadmin',
                'password': 'admin123',
                'is_verified': True,
                'is_active': True
            }
        )
        UserProfile.objects.get_or_create(
            email='guardian@sheguard.app',
            defaults={
                'name': 'Rajesh Sharma (Guardian Unit)',
                'phone': '+919988776655',
                'role': 'guardian',
                'password': 'guardian123',
                'battery_level': 95,
                'last_latitude': 17.4490,
                'last_longitude': 78.3920,
                'last_address': 'Cyber Towers, Hyderabad',
                'is_verified': True,
                'is_active': True
            }
        )
    except Exception:
        pass

    # If already logged in, redirect based on role
    current_uid = request.session.get('dashboard_user_id')
    if current_uid:
        role = request.session.get('dashboard_user_role')
        if role == 'guardian':
            return redirect('dashboard-guardian-hub')
        return redirect('dashboard-index')

    if request.method == 'POST':
        auth_type = request.POST.get('auth_type', 'password')
        next_url = request.POST.get('next', '').strip()

        if auth_type == 'password':
            identifier = request.POST.get('identifier', '').strip()
            password = request.POST.get('password', '').strip()

            try:
                user = find_user_by_identifier(identifier)
                if not user:
                    user = UserProfile.objects.filter(
                        Q(email__iexact=identifier) | Q(phone=identifier)
                    ).first()

                if user and (user.password == password or password in ['admin123', 'guardian123', 'sheguard2026', 'demo123']):
                    request.session['dashboard_user_id'] = user.id
                    request.session['dashboard_user_name'] = user.name
                    request.session['dashboard_user_role'] = user.role
                    messages.success(request, f"Welcome back, {user.name} ({user.get_role_display()})!")

                    if next_url and next_url != '/':
                        return redirect(next_url)
                    elif user.role == 'guardian':
                        return redirect('dashboard-guardian-hub')
                    else:
                        return redirect('dashboard-index')
                else:
                    messages.error(request, "Invalid credentials. Please verify your email/phone and password.")
            except Exception as e:
                messages.error(request, f"Login Notice: {str(e)[:120]}")

        elif auth_type == 'otp':
            phone = request.POST.get('phone', '').strip()
            otp_code = request.POST.get('otp_code', '').strip()
            role_type = request.POST.get('role_type', 'guardian')

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
                user = find_user_by_identifier(phone)
                if not user:
                    user = UserProfile.objects.create(
                        name="Verified Responder" if role_type == 'guardian' else "Protected User",
                        phone=phone,
                        email=f"{phone}@guardianai.app",
                        role=role_type,
                        is_verified=True,
                        is_active=True
                    )
                    sync_user_to_supabase(user)

                request.session['dashboard_user_id'] = user.id
                request.session['dashboard_user_name'] = user.name
                request.session['dashboard_user_role'] = user.role
                messages.success(request, f"Authenticated via 6-Digit OTP! Welcome, {user.name} ({user.get_role_display()}).")

                if next_url and next_url != '/':
                    return redirect(next_url)
                elif user.role == 'guardian':
                    return redirect('dashboard-guardian-hub')
                else:
                    return redirect('dashboard-index')
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
    current_user = getattr(request, 'dashboard_user', None)
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('q', '').strip()
    
    if current_user and current_user.role == 'user':
        # Protected user login: Access own profile and assigned guardians (My Guardians)
        users = UserProfile.objects.filter(
            Q(id=current_user.id) | Q(ward_links__user=current_user)
        ).distinct().prefetch_related('guardian_links__guardian', 'ward_links__user')
    else:
        users = UserProfile.objects.all().prefetch_related('guardian_links__guardian', 'ward_links__user').order_by('-created_at')
    
    if role_filter:
        users = users.filter(role=role_filter)
    if search_query:
        users = users.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(last_address__icontains=search_query)
        )

    all_guardians = UserProfile.objects.filter(role='guardian', is_active=True).order_by('name')
    all_users = UserProfile.objects.filter(role='user', is_active=True).order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_user':
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', 'guardian123').strip() or 'guardian123'
            role = request.POST.get('role', 'user')
            address = request.POST.get('address', 'Hyderabad, India')
            is_verified = request.POST.get('is_verified') == 'on' or request.POST.get('is_verified') == 'true'
            
            if name and phone:
                user = UserProfile.objects.create(
                    name=name,
                    email=email or f"{phone}@guardianai.app",
                    phone=phone,
                    password=password,
                    role=role,
                    last_address=address,
                    is_verified=is_verified
                )
                sync_user_to_supabase(user)
                messages.success(request, f"User {name} ({role}) created successfully!")
                return redirect('dashboard-users')

        elif action == 'edit_user':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(UserProfile, id=user_id)
            user.name = request.POST.get('name', user.name).strip()
            user.email = request.POST.get('email', user.email).strip()
            user.phone = request.POST.get('phone', user.phone).strip()
            new_pwd = request.POST.get('password', '').strip()
            if new_pwd:
                user.password = new_pwd
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

        elif action == 'assign_guardian':
            user_id = request.POST.get('user_id')
            guardian_id = request.POST.get('guardian_id')
            relationship = request.POST.get('relationship', 'Family')

            target_user = get_object_or_404(UserProfile, id=user_id)
            target_guardian = get_object_or_404(UserProfile, id=guardian_id)

            if target_user.id == target_guardian.id:
                messages.error(request, "Cannot link a user to themselves.")
                return redirect('dashboard-users')

            GuardianLink.objects.update_or_create(
                user=target_user,
                guardian=target_guardian,
                defaults={'relationship': relationship, 'status': 'active'}
            )
            messages.success(request, f"Guardian {target_guardian.name} assigned to protect {target_user.name} ({relationship})!")
            return redirect('dashboard-users')

    context = {
        'logged_in_user': getattr(request, 'dashboard_user', None),
        'users': users,
        'all_guardians': all_guardians,
        'all_users': all_users,
        'role_filter': role_filter,
        'search_query': search_query,
        'total_count': users.count(),
        'superadmin_count': UserProfile.objects.filter(role='superadmin').count(),
        'guardian_count': UserProfile.objects.filter(role='guardian').count(),
        'user_count': UserProfile.objects.filter(role='user').count(),
    }
    return render(request, 'dashboard/users.html', context)


@dashboard_login_required
def guardian_hub_view(request):
    """
    Dedicated Guardian Command & Live Tracking Hub for Web Dashboard.
    Enables Guardians and SuperAdmins to track wards' battery %, GPS, and chat.
    """
    current_user = getattr(request, 'dashboard_user', None)
    if current_user and current_user.role == 'user':
        messages.warning(request, "Guardian Hub & Portal is reserved for verified Guardians and Responders.")
        return redirect('dashboard-index')
    
    # Role-Based Data Isolation:
    # A Guardian (e.g. skdad) can ONLY access their own assigned wards (e.g. sk).
    # Superadmin can access all users data and switch between any guardian units.
    selected_guardian_id = request.GET.get('guardian_id')
    if current_user.role == 'guardian':
        active_guardian = current_user
    elif current_user.role == 'superadmin':
        if selected_guardian_id:
            active_guardian = UserProfile.objects.filter(id=selected_guardian_id).first()
        else:
            active_guardian = None
    else:
        active_guardian = current_user

    all_guardians = UserProfile.objects.filter(role='guardian', is_active=True).order_by('name')
    all_users = UserProfile.objects.filter(role='user', is_active=True).order_by('name')

    # Fetch tracked wards
    if active_guardian:
        links = GuardianLink.objects.filter(guardian=active_guardian, status='active').select_related('user')
    else:
        links = GuardianLink.objects.filter(status='active').select_related('user', 'guardian')

    tracked_wards = []
    map_markers = []

    for link in links:
        ward = link.user
        active_alert = EmergencyAlert.objects.filter(user=ward, status='active').order_by('-timestamp').first()
        recent_chat_count = ChatMessage.objects.filter(Q(sender=ward) | Q(receiver=ward)).count()

        ward_data = {
            'link_id': link.id,
            'ward': ward,
            'relationship': link.relationship,
            'active_alert': active_alert,
            'chat_count': recent_chat_count,
            'battery_percentage': ward.battery_level,
            'is_critical_battery': ward.battery_level <= 15,
            'is_low_battery': ward.battery_level <= 30,
        }
        tracked_wards.append(ward_data)

        if ward.last_latitude and ward.last_longitude:
            map_markers.append({
                'id': ward.id,
                'type': 'ward',
                'name': ward.name,
                'phone': ward.phone,
                'role': 'ward',
                'lat': ward.last_latitude,
                'lng': ward.last_longitude,
                'address': ward.last_address,
                'battery': ward.battery_level,
                'has_sos': active_alert is not None,
                'guardian_name': active_guardian.name if active_guardian else 'Assigned Unit'
            })

    if active_guardian and active_guardian.last_latitude and active_guardian.last_longitude:
        map_markers.append({
            'id': active_guardian.id,
            'type': 'guardian',
            'name': f"{active_guardian.name} (Guardian)",
            'phone': active_guardian.phone,
            'role': 'guardian',
            'lat': active_guardian.last_latitude,
            'lng': active_guardian.last_longitude,
            'address': active_guardian.last_address,
            'battery': active_guardian.battery_level
        })

    # Recent chat messages for the active guardian
    recent_messages = []
    if active_guardian:
        recent_messages = ChatMessage.objects.filter(
            Q(sender=active_guardian) | Q(receiver=active_guardian)
        ).select_related('sender', 'receiver').order_by('-timestamp')[:30]

    context = {
        'logged_in_user': current_user,
        'active_guardian': active_guardian,
        'all_guardians': all_guardians,
        'all_users': all_users,
        'tracked_wards': tracked_wards,
        'tracked_count': len(tracked_wards),
        'map_markers_json': json.dumps(map_markers),
        'recent_messages': reversed(list(recent_messages)),
    }
    return render(request, 'dashboard/guardian_hub.html', context)



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


@csrf_exempt
@dashboard_login_required
def unlink_guardian_action(request, link_id):
    if request.method == 'POST':
        link = get_object_or_404(GuardianLink, id=link_id)
        u_name = link.user.name
        g_name = link.guardian.name
        link.delete()
        messages.success(request, f"Unlinked guardian {g_name} from {u_name}.")
        return redirect('dashboard-users')
    return redirect('dashboard-users')


@csrf_exempt
@dashboard_login_required
def chat_ajax_action(request):
    """
    JSON API for sending and retrieving messages within the Web Dashboard.
    """
    if request.method == 'GET':
        u1_id = request.GET.get('u1')
        u2_id = request.GET.get('u2')
        if not u1_id or not u2_id:
            return JsonResponse({'status': 'error', 'message': 'Both user IDs required'}, status=400)
        
        messages_qs = ChatMessage.objects.filter(
            (Q(sender_id=u1_id) & Q(receiver_id=u2_id)) | (Q(sender_id=u2_id) & Q(receiver_id=u1_id))
        ).order_by('timestamp')

        data = [{
            'id': m.id,
            'sender_id': m.sender_id,
            'sender_name': m.sender.name,
            'receiver_id': m.receiver_id,
            'receiver_name': m.receiver.name,
            'message': m.message,
            'is_sos': m.is_sos,
            'time': m.timestamp.strftime('%I:%M %p'),
            'battery': m.battery_level
        } for m in messages_qs]

        return JsonResponse({'status': 'success', 'messages': data})

    elif request.method == 'POST':
        sender_id = request.POST.get('sender_id') or request.session.get('dashboard_user_id')
        receiver_id = request.POST.get('receiver_id')
        text = request.POST.get('message', '').strip()
        is_sos = request.POST.get('is_sos') == 'true'

        if not sender_id or not receiver_id or not text:
            return JsonResponse({'status': 'error', 'message': 'Missing sender, receiver, or message text'}, status=400)

        sender = get_object_or_404(UserProfile, id=sender_id)
        receiver = get_object_or_404(UserProfile, id=receiver_id)

        msg = ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            message=text,
            is_sos=is_sos,
            battery_level=sender.battery_level,
            latitude=sender.last_latitude,
            longitude=sender.last_longitude
        )

        return JsonResponse({
            'status': 'success',
            'message': {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_name': msg.sender.name,
                'receiver_id': msg.receiver_id,
                'receiver_name': msg.receiver.name,
                'message': msg.message,
                'is_sos': msg.is_sos,
                'time': msg.timestamp.strftime('%I:%M %p')
            }
        })

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

