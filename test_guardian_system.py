import os
import sys
import django
import json

# Ensure UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardian_backend.settings')
django.setup()


from guardian_api.models import UserProfile, GuardianLink, ChatMessage, EmergencyAlert
from django.test import Client

def run_tests():
    print("🚀 Starting Guardian Role, Tracking, and Chat System Tests...")
    client = Client()

    # 1. Setup Test Users
    user, _ = UserProfile.objects.update_or_create(
        phone="+919876543210",
        defaults={
            'name': 'Priya Sharma (Protected User)',
            'email': 'priya@example.com',
            'role': 'user',
            'battery_level': 78,
            'last_latitude': 17.4482,
            'last_longitude': 78.3914,
            'last_address': 'Madhapur, Hitech City, Hyderabad',
            'is_verified': True
        }
    )
    print(f"✅ Created/Loaded Protected User: {user.name} (Battery: {user.battery_level}%)")

    guardian, _ = UserProfile.objects.update_or_create(
        phone="+919988776655",
        defaults={
            'name': 'Rajesh Sharma (Guardian Unit)',
            'email': 'rajesh@example.com',
            'role': 'guardian',
            'battery_level': 95,
            'last_latitude': 17.4490,
            'last_longitude': 78.3920,
            'last_address': 'Cyber Towers, Hyderabad',
            'is_verified': True
        }
    )
    print(f"✅ Created/Loaded Guardian: {guardian.name} (Battery: {guardian.battery_level}%)")

    # 2. Test Linking Guardian via API
    res = client.post('/api/guardians/link/', data=json.dumps({
        'user_phone': user.phone,
        'guardian_phone': guardian.phone,
        'guardian_name': guardian.name,
        'relationship': 'Father'
    }), content_type='application/json')
    assert res.status_code in [200, 201], f"Link failed: {res.content}"
    print(f"✅ Guardian Link API: {res.json()['message']}")

    # 3. Test Guardian Tracking Wards (Battery % & GPS Location)
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={guardian.phone}')
    assert res.status_code == 200, f"Tracked wards failed: {res.content}"
    data = res.json()
    assert data['tracked_wards_count'] >= 1, "No wards found for guardian"
    ward_info = data['wards'][0]
    print(f"✅ Guardian Wards Radar API: Ward={ward_info['name']}, Battery={ward_info['battery_level']}%, Status={ward_info['battery_status']}, Location=({ward_info['latitude']}, {ward_info['longitude']})")

    # 4. Test Chat Message from User to Guardian
    res = client.post('/api/chat/send/', data=json.dumps({
        'sender_phone': user.phone,
        'receiver_phone': guardian.phone,
        'message': 'Dad, I have reached the metro station safely!',
        'battery_level': 75,
        'latitude': 17.4485,
        'longitude': 78.3918
    }), content_type='application/json')
    assert res.status_code == 201, f"Send chat failed: {res.content}"
    print(f"✅ User Sent Chat: \"Dad, I have reached the metro station safely!\"")

    # 5. Test Chat Message from Guardian to User
    res = client.post('/api/chat/send/', data=json.dumps({
        'sender_phone': guardian.phone,
        'receiver_phone': user.phone,
        'message': 'Great! Stay on the main road and keep your battery charged.',
        'battery_level': 94
    }), content_type='application/json')
    assert res.status_code == 201, f"Send chat failed: {res.content}"
    print(f"✅ Guardian Sent Chat: \"Great! Stay on the main road and keep your battery charged.\"")

    # 6. Test Chat History Retrieval
    res = client.get(f'/api/chat/messages/?user1={user.phone}&user2={guardian.phone}')
    assert res.status_code == 200, f"Get chat failed: {res.content}"
    chat_data = res.json()
    assert len(chat_data['messages']) >= 2, "Chat history missing messages"
    print(f"✅ Chat History API: {len(chat_data['messages'])} message(s) retrieved successfully")

    # 7. Test Location & Battery Ping Sync
    res = client.post('/api/location/ping/', data=json.dumps({
        'phone': user.phone,
        'latitude': 17.4501,
        'longitude': 78.3950,
        'address': 'Inorbit Mall Road, Madhapur',
        'battery_level': 72
    }), content_type='application/json')
    assert res.status_code == 200, f"Ping failed: {res.content}"
    print(f"✅ Real-time Telemetry Ping: Updated user to 72% battery at Inorbit Mall Road")

    # Re-verify Guardian sees updated battery & location
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={guardian.phone}')
    ward_info = res.json()['wards'][0]
    assert ward_info['battery_level'] == 72
    assert ward_info['address'] == 'Inorbit Mall Road, Madhapur'
    print(f"✅ Guardian Radar Verified: Live Telemetry is {ward_info['battery_level']}% battery at {ward_info['address']}")

    # 8. Test Regular User access to "My Guardians" API
    res = client.get(f'/api/guardians/my-guardians/?phone={user.phone}')
    assert res.status_code == 200, f"My Guardians failed: {res.content}"
    user_guardians = res.json()['links']
    assert len(user_guardians) >= 1, "User should see their assigned guardians"
    print(f"✅ User 'My Guardians' Access Verified: {len(user_guardians)} guardian(s) protecting user")

    # 9. Test Regular User CANNOT access Guardian Portal / Tracked Wards (Forbidden 403)
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={user.phone}')
    assert res.status_code == 403, f"Regular user should be denied access to Guardian Portal: {res.status_code}"
    print(f"✅ User Guardian Portal Removal Verified: 403 Forbidden correctly returned for regular users")

    # 10. Scenario Test: User 'sk' with guardian 'skdad'; another user 'other_user' with guardian 'other_guardian'
    sk_user, _ = UserProfile.objects.update_or_create(
        phone="+919100000001",
        defaults={'name': 'SK User', 'email': 'sk@sheguard.app', 'role': 'user', 'battery_level': 88}
    )
    skdad_guardian, _ = UserProfile.objects.update_or_create(
        phone="+919200000002",
        defaults={'name': 'SK Dad Guardian', 'email': 'skdad@sheguard.app', 'role': 'guardian', 'battery_level': 99}
    )
    other_user, _ = UserProfile.objects.update_or_create(
        phone="+919300000003",
        defaults={'name': 'Other User', 'email': 'other_u@sheguard.app', 'role': 'user', 'battery_level': 65}
    )
    other_guardian, _ = UserProfile.objects.update_or_create(
        phone="+919400000004",
        defaults={'name': 'Other Guardian', 'email': 'other_g@sheguard.app', 'role': 'guardian', 'battery_level': 90}
    )
    superadmin, _ = UserProfile.objects.update_or_create(
        phone="+919876500000",
        defaults={'name': 'Chief SuperAdmin', 'email': 'admin@sheguard.app', 'role': 'superadmin'}
    )

    # Link sk -> skdad
    GuardianLink.objects.update_or_create(user=sk_user, guardian=skdad_guardian, defaults={'relationship': 'Father', 'status': 'active'})
    # Link other_user -> other_guardian
    GuardianLink.objects.update_or_create(user=other_user, guardian=other_guardian, defaults={'relationship': 'Brother', 'status': 'active'})

    # 10a. skdad can ONLY see sk
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={skdad_guardian.phone}')
    assert res.status_code == 200
    skdad_wards = res.json()['wards']
    skdad_ward_phones = [w['phone'] for w in skdad_wards]
    assert sk_user.phone in skdad_ward_phones, "skdad must see sk"
    assert other_user.phone not in skdad_ward_phones, "skdad must NOT see other_user"
    print(f"✅ Strict Guardian Isolation Verified: skdad ONLY sees their assigned ward ({sk_user.name}), cannot see other wards")

    # 10b. other_guardian can ONLY see other_user
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={other_guardian.phone}')
    assert res.status_code == 200
    other_g_wards = res.json()['wards']
    other_g_ward_phones = [w['phone'] for w in other_g_wards]
    assert other_user.phone in other_g_ward_phones, "other_guardian must see other_user"
    assert sk_user.phone not in other_g_ward_phones, "other_guardian must NOT see sk"
    print(f"✅ Strict Guardian Isolation Verified: other_guardian ONLY sees {other_user.name}")

    # 10c. sk (user) CANNOT access guardian portal
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={sk_user.phone}')
    assert res.status_code == 403, "sk (user role) must be forbidden from accessing Guardian Portal"
    print(f"✅ User Access Block Verified: sk (user) gets 403 Forbidden on Guardian Portal")

    # 10d. superadmin can access ALL users data
    res = client.get(f'/api/guardians/tracked-wards/?guardian_phone={superadmin.phone}')
    assert res.status_code == 200
    admin_wards = res.json()['wards']
    admin_ward_phones = [w['phone'] for w in admin_wards]
    assert sk_user.phone in admin_ward_phones, "superadmin must see sk"
    assert other_user.phone in admin_ward_phones, "superadmin must see other_user"
    print(f"✅ SuperAdmin Omniscient Access Verified: SuperAdmin accessed all {len(admin_wards)} users data across the system")

    # 11. Location History / 24h Trail Replay Tests
    print("\n📍 Testing 24h Location History & Replay Playback API...")

    # 11a. skdad queries sk's 24h trail -> 200 OK
    res = client.get(f'/api/location/history/?ward_phone={sk_user.phone}&guardian_phone={skdad_guardian.phone}&hours=24')
    assert res.status_code == 200, f"History request failed: {res.content}"
    data = res.json()
    assert data['status'] == 'success'
    assert len(data['trail']) > 0, "Trail points should be populated"
    print(f"✅ Guardian 24h Replay Access Verified: Retrieved {data['total_points']} trail points for ward {data['ward']['name']}")

    # 11b. Send a real location ping for sk and check it appears in history
    client.post('/api/location/ping/', data=json.dumps({
        'phone': sk_user.phone,
        'latitude': 17.4495,
        'longitude': 78.3935,
        'address': 'Kavuri Hills Junction',
        'battery_level': 82
    }), content_type='application/json')

    # Trigger an emergency alert to check incident marker
    alert_res = client.post('/api/sos/trigger/', data=json.dumps({
        'phone': sk_user.phone,
        'latitude': 17.4496,
        'longitude': 78.3936,
        'address': 'Kavuri Hills Junction (Incident Point)',
        'trigger_source': 'button',
        'battery_level': 81
    }), content_type='application/json')
    assert alert_res.status_code == 201

    res = client.get(f'/api/location/history/?ward_phone={sk_user.phone}&guardian_phone={skdad_guardian.phone}&hours=24')
    assert res.status_code == 200
    data = res.json()
    assert data['incident_count'] >= 1, "Incident point should be flagged"
    incident_pts = [pt for pt in data['trail'] if pt.get('is_incident')]
    assert len(incident_pts) >= 1
    print(f"✅ Incident Beacon Correlation Verified: {len(incident_pts)} point(s) flagged with SOS incident beacon")

    # 11c. Unauthorized guardian (other_guardian) tries to access sk's trail -> 403 Forbidden
    res = client.get(f'/api/location/history/?ward_phone={sk_user.phone}&guardian_phone={other_guardian.phone}&hours=24')
    assert res.status_code == 403, f"Expected 403 Forbidden for unauthorized guardian: {res.status_code}"
    print(f"✅ Location Trail Isolation Verified: Unauthorized guardian received 403 Forbidden")

    # 11d. Ward querying her own trail -> 200 OK
    res = client.get(f'/api/location/history/?ward_phone={sk_user.phone}&guardian_phone={sk_user.phone}&hours=24')
    assert res.status_code == 200
    print(f"✅ Ward Self-Inspection Verified: User can inspect her own 24h trail")

    # 11e. SuperAdmin querying ward trail -> 200 OK
    res = client.get(f'/api/location/history/?ward_phone={sk_user.phone}&guardian_phone={superadmin.phone}&hours=24')
    assert res.status_code == 200
    print(f"✅ SuperAdmin Replay Access Verified: SuperAdmin can inspect any ward's trail")

    print("\n🎉 ALL GUARDIAN SYSTEM & 24H REPLAY TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
