from django.urls import path
from .views import RegisterView, LoginView, UserListView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/users/', UserListView.as_view(), name='users'),
]