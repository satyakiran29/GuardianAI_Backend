from django.urls import path
from .views import (
    SendOtpView,
    VerifyOtpView,
    RegisterView,
    LoginView,
    SosTriggerView,
    SosResolveView,
    LocationPingView,
    UserListView,
    EmergencyContactsView,
    HelplinesView,
    DashboardStatsApiView
)

urlpatterns = [
    # Authentication & OTP
    path('auth/send-otp/', SendOtpView.as_view(), name='api-send-otp'),
    path('auth/verify-otp/', VerifyOtpView.as_view(), name='api-verify-otp'),
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', LoginView.as_view(), name='api-login'),

    # SOS & Emergency Telemetry
    path('sos/trigger/', SosTriggerView.as_view(), name='api-sos-trigger'),
    path('sos/resolve/', SosResolveView.as_view(), name='api-sos-resolve'),
    path('location/ping/', LocationPingView.as_view(), name='api-location-ping'),

    # Users & Contacts
    path('users/', UserListView.as_view(), name='api-users'),
    path('contacts/', EmergencyContactsView.as_view(), name='api-contacts'),
    path('helplines/', HelplinesView.as_view(), name='api-helplines'),

    # Dashboard Telemetry
    path('dashboard/stats/', DashboardStatsApiView.as_view(), name='api-dashboard-stats'),
]
