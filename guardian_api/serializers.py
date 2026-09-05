from rest_framework import serializers
from .models import UserProfile, EmergencyAlert, OtpRecord, EmergencyContact, TripLog, GuardianLink, ChatMessage, LocationHistory

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = '__all__'


class GuardianLinkSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_battery = serializers.IntegerField(source='user.battery_level', read_only=True)
    user_lat = serializers.FloatField(source='user.last_latitude', read_only=True)
    user_lng = serializers.FloatField(source='user.last_longitude', read_only=True)
    user_address = serializers.CharField(source='user.last_address', read_only=True)

    guardian_name = serializers.CharField(source='guardian.name', read_only=True)
    guardian_phone = serializers.CharField(source='guardian.phone', read_only=True)
    guardian_email = serializers.CharField(source='guardian.email', read_only=True)

    class Meta:
        model = GuardianLink
        fields = [
            'id', 'user', 'guardian', 'relationship', 'status', 'created_at',
            'user_name', 'user_phone', 'user_email', 'user_battery', 'user_lat', 'user_lng', 'user_address',
            'guardian_name', 'guardian_phone', 'guardian_email'
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.name', read_only=True)
    sender_phone = serializers.CharField(source='sender.phone', read_only=True)
    receiver_name = serializers.CharField(source='receiver.name', read_only=True)
    receiver_phone = serializers.CharField(source='receiver.phone', read_only=True)
    formatted_time = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'receiver', 'sender_name', 'sender_phone',
            'receiver_name', 'receiver_phone', 'message', 'is_sos',
            'latitude', 'longitude', 'battery_level', 'is_read', 'timestamp', 'formatted_time'
        ]

    def get_formatted_time(self, obj):
        return obj.timestamp.strftime('%I:%M %p')


class UserProfileSerializer(serializers.ModelSerializer):
    contacts = EmergencyContactSerializer(many=True, read_only=True)
    contact_count = serializers.SerializerMethodField()
    guardian_count = serializers.SerializerMethodField()
    ward_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'name', 'email', 'phone', 'role', 'is_verified', 'is_active',
            'last_latitude', 'last_longitude', 'last_address', 'battery_level',
            'fcm_token', 'created_at', 'updated_at', 'contacts', 'contact_count',
            'guardian_count', 'ward_count'
        ]

    def get_contact_count(self, obj):
        return obj.contacts.count()

    def get_guardian_count(self, obj):
        return obj.guardian_links.count()

    def get_ward_count(self, obj):
        return obj.ward_links.count()


class EmergencyAlertSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    responder_name = serializers.CharField(source='responder.name', read_only=True, default=None)

    class Meta:
        model = EmergencyAlert
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'user_role', 'latitude', 'longitude',
            'address', 'trigger_source', 'status', 'siren_active', 'battery_level',
            'responder', 'responder_name', 'timestamp', 'resolved_at', 'notes'
        ]


class OtpRecordSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = OtpRecord
        fields = ['id', 'target', 'otp_code', 'purpose', 'is_verified', 'created_at', 'expires_at', 'is_expired']

    def get_is_expired(self, obj):
        return obj.is_expired()


class TripLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = TripLog
        fields = '__all__'


class LocationHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    formatted_time = serializers.SerializerMethodField()

    class Meta:
        model = LocationHistory
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'latitude', 'longitude',
            'address', 'battery_level', 'timestamp', 'formatted_time'
        ]

    def get_formatted_time(self, obj):
        return obj.timestamp.strftime('%I:%M %p')

