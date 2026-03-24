from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    AdvertisementCreateView,
    AdvertisementDetailView,
    AdvertisementListView,
    AdvertisementUpdateView,
    accept_response_view,
    confirm_registration_view,
    create_response_view,
    delete_response_view,
    login_view,
    response_list_view,
    signup_view,
)

app_name = "board"

urlpatterns = [
    path("", AdvertisementListView.as_view(), name="advertisement_list"),
    path("signup/", signup_view, name="signup"),
    path("confirm-registration/", confirm_registration_view, name="confirm_registration"),
    path("login/", login_view, name="login"),
    path("logout/", LogoutView.as_view(next_page="board:advertisement_list"), name="logout"),
    path("advertisements/create/", AdvertisementCreateView.as_view(), name="advertisement_create"),
    path("advertisements/<int:pk>/", AdvertisementDetailView.as_view(), name="advertisement_detail"),
    path("advertisements/<int:pk>/edit/", AdvertisementUpdateView.as_view(), name="advertisement_edit"),
    path("advertisements/<int:pk>/respond/", create_response_view, name="create_response"),
    path("responses/", response_list_view, name="response_list"),
    path("responses/<int:pk>/accept/", accept_response_view, name="accept_response"),
    path("responses/<int:pk>/delete/", delete_response_view, name="delete_response"),
]
