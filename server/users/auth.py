from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from users.serializers import MyTokenObtainPairSerializer, UserSerializer
from users.models import User
from users.services import *


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['POST'])
def refreshToken(request):
    old_refresh = request.data['refresh']
    user = User.objects.get(email=request.data['email'])

    if old_refresh == user.refresh:
        # Blacklist old refresh token
        try:
            RefreshToken(old_refresh).blacklist()
        except TokenError:
            pass

        # Refresh token
        refresh = RefreshToken.for_user(user)
        token_pair = {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }

        # Update last_login & refresh field
        user.refresh = token_pair['refresh']
        user.save(update_fields=['refresh'])

        return Response(token_pair)
    else:
        message = {'detail': 'Refresh token is invalid or expired'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def loginWithGoogle(request):
    code = request.query_params.get('code')
    error = request.query_params.get('error')

    # Handle error, invalid request
    if error or not code:
        # Check if error, redirect to login page
        params = urlencode({'error': error})
        login_url = f'{settings.BASE_FRONTEND_URL}/login'
        return redirect(f'{login_url}?{params}')

    api_uri = reverse('api-v1:users:auth:login-with-google')
    redirect_uri = f'{settings.BASE_BACKEND_URL}{api_uri}'

    # Exchange `code` for an `access_token` from GG oauth2 server
    access_token = request_gg_access_token(
        code=code, redirect_uri=redirect_uri)

    gg_user_data = request_gg_user_info(access_token=access_token)

    # We use get-or-create logic here for the sake of the example.
    # We don't have a sign-up flow.
    user, _ = get_or_create_user(data=gg_user_data)
    token_pair = jwt_login(user=user)

    # Get user_data and Add to token_pair
    serializer = UserSerializer(user, many=False)
    user_data = {key: val for (key, val) in serializer.data.items()}
    user_data = {**user_data, **token_pair}

    return Response(user_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def loginWithFacebook(request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')

    # Handle error, invalid request
    login_url = f'{settings.BASE_FRONTEND_URL}/login'
    if error or not code:
        # Check if error, redirect to login page
        # error_reason=user_denied&error=access_denied&error_description=Permissions+error.
        params = urlencode({'error': error})
        return redirect(f'{login_url}?{params}')
    if state != settings.SECRET_FACEBOOK_STATE:
        # Check if client state != server state, redirect to login page
        params = urlencode({'error': 'Invalid Facebook Secret state'})
        return redirect(f'{login_url}?{params}')

    api_uri = reverse('api-v1:users:auth:login-with-facebook')
    redirect_uri = f'{settings.BASE_BACKEND_URL}{api_uri}'

    # Exchange `code` for an `access_token` from FB oauth2 server
    access_token = request_fb_access_token(
        code=code, redirect_uri=redirect_uri)

    # Get `user_id` using `access_token`
    user_id = request_fb_user_id(access_token=access_token)

    fb_user_data = request_fb_user_info(
        access_token=access_token, user_id=user_id)

    # We use get-or-create logic here for the sake of the example.
    # We don't have a sign-up flow.
    user, _ = get_or_create_user(data=fb_user_data)
    token_pair = jwt_login(user=user)

    # Get user_data and Add to token_pair
    serializer = UserSerializer(user, many=False)
    user_data = {key: val for (key, val) in serializer.data.items()}
    user_data = {**user_data, **token_pair}

    return Response(user_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logout(request):
    user = request.user

    # Blacklist old refresh token
    try:
        RefreshToken(user.refresh).blacklist()
    except TokenError:
        pass

    # Remove refresh from user model
    user.refresh = ""
    user.save(update_fields=['refresh'])

    return Response(status=status.HTTP_202_ACCEPTED)
