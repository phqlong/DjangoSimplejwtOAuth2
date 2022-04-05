from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import *
from users.auth import *

auth_patterns = [
    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', refreshToken, name='refresh-token'),

    path('login/google/', loginWithGoogle, name='login-with-google'),
    path('login/facebook/', loginWithFacebook, name='login-with-facebook'),

    path('login/', MyTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout, name='logout'),
]

urlpatterns = [
    path('auth/', include((auth_patterns, 'auth'))),
    
    path('register/', registerUser, name='register'),

    path('profile/', getMyProfile, name="users-profile"),
    path('profile/update/', updateMyProfile, name="user-profile-update"),
    path('', getUsers, name="users"),

    path('<str:pk>/', getUserById, name='user'),

    path('update/<str:pk>/', updateMyProfile, name='user-update'),

    path('delete/<str:pk>/', deleteUserById, name='user-delete'),
]
