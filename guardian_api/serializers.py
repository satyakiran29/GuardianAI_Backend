from rest_framework import serializers
from .models import UserProfile, EmergencyAlert, OtpRecord, EmergencyContact, TripLog

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    contacts = EmergencyContactSerializer(many=True, read_only=True)
    contact_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'name', 'email', 'phone', 'role', 'is_verified', 'is_active',
            'last_latitude', 'last_longitude', 'last_address', 'battery_level',
            'fcm_token', 'created_at', 'updated_at', 'contacts', 'contact_count'
        ]

    def get_contact_count(self, obj):
        return obj.contacts.count()


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
