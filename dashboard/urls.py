from django.urls import path
from .views import (
    login_view,
    logout_view,
    index,
    users_view,
    alerts_view,
    otp_view,
    dispatch_alert_action,
    resolve_alert_action,
    update_user_role_action,
    delete_user_action,
    export_users_csv
)

urlpatterns = [
    path('login/', login_view, name='dashboard-login'),
    path('logout/', logout_view, name='dashboard-logout'),
    path('', index, name='dashboard-index'),
    path('users/', users_view, name='dashboard-users'),
    path('users/export/csv/', export_users_csv, name='dashboard-export-users-csv'),
    path('alerts/', alerts_view, name='dashboard-alerts'),
    path('otp/', otp_view, name='dashboard-otp'),
    
    # Action hooks
    path('alerts/<int:alert_id>/dispatch/', dispatch_alert_action, name='dashboard-dispatch-alert'),
    path('alerts/<int:alert_id>/resolve/', resolve_alert_action, name='dashboard-resolve-alert'),
    path('users/<int:user_id>/role/', update_user_role_action, name='dashboard-update-role'),
    path('users/<int:user_id>/delete/', delete_user_action, name='dashboard-delete-user'),
]
