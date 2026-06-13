# apps/web/college_admin/urls.py
from django.urls import path
from apps.web.college_admin.views import (
    CollegeSettingsView,
    InviteUserView,
    SubscriptionStatusView,
    UserDetailView,
    UserListView,
)

urlpatterns = [
    path("settings/",              CollegeSettingsView.as_view(),  name="college_settings"),
    path("users/",                 UserListView.as_view(),         name="user_list"),
    path("users/invite/",          InviteUserView.as_view(),       name="invite_user"),
    path("users/<uuid:user_id>/",  UserDetailView.as_view(),       name="user_detail"),
    path("subscription/",          SubscriptionStatusView.as_view(), name="subscription_status"),
]
