from django.urls import path
from .views import (
    SendOtpView,
    VerifyOtpView,
    RegisterView,
    UpdateProfileView,
    LoginView,
    SosTriggerView,
    SosResolveView,
    LocationPingView,
    UserListView,
    EmergencyContactsView,
    HelplinesView,
    DashboardStatsApiView,
    PingView,
    GuardianLinkView,
    GuardianTrackedWardsView,
    ChatMessagesView
)

urlpatterns = [
    # Health & 14-min Keep-Alive Ping
    path('ping/', PingView.as_view(), name='api-ping'),
    path('health/', PingView.as_view(), name='api-health'),

    # Authentication & OTP
    path('auth/send-otp/', SendOtpView.as_view(), name='api-send-otp'),
    path('auth/verify-otp/', VerifyOtpView.as_view(), name='api-verify-otp'),
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/profile/update/', UpdateProfileView.as_view(), name='api-profile-update'),
    path('auth/login/', LoginView.as_view(), name='api-login'),

    # SOS & Emergency Telemetry
    path('sos/trigger/', SosTriggerView.as_view(), name='api-sos-trigger'),
    path('sos/resolve/', SosResolveView.as_view(), name='api-sos-resolve'),
    path('location/ping/', LocationPingView.as_view(), name='api-location-ping'),

    # Users & Contacts
    path('users/', UserListView.as_view(), name='api-users'),
    path('contacts/', EmergencyContactsView.as_view(), name='api-contacts'),
    path('helplines/', HelplinesView.as_view(), name='api-helplines'),

    # Guardian Role & Live Tracking
    path('guardians/link/', GuardianLinkView.as_view(), name='api-guardians-link'),
    path('guardians/my-guardians/', GuardianLinkView.as_view(), name='api-my-guardians'),
    path('guardians/tracked-wards/', GuardianTrackedWardsView.as_view(), name='api-tracked-wards'),

    # Real-Time Safety Chat
    path('chat/messages/', ChatMessagesView.as_view(), name='api-chat-messages'),
    path('chat/send/', ChatMessagesView.as_view(), name='api-chat-send'),

    # Dashboard Telemetry
    path('dashboard/stats/', DashboardStatsApiView.as_view(), name='api-dashboard-stats'),
]

