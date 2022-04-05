import requests
from typing import Dict, Tuple, Any
from collections import OrderedDict

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from users.models import User

GOOGLE_ID_TOKEN_INFO_URL = 'https://www.googleapis.com/oauth2/v3/tokeninfo'
GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

FACEBOOK_ACCESS_TOKEN_OBTAIN_URL = 'https://graph.facebook.com/v13.0/oauth/access_token'
FACEBOOK_USER_ID_URL = 'https://graph.facebook.com/v13.0/me'
FACEBOOK_USER_INFO_URL = 'https://graph.facebook.com/v13.0'


def validate_google_id_token(*, id_token: str) -> bool:
    # Reference: https://developers.google.com/identity/sign-in/web/backend-auth#verify-the-integrity-of-the-id-token
    params = {'id_token': id_token}

    response = requests.get(GOOGLE_ID_TOKEN_INFO_URL, params=params)

    if response.ok:
        audience = response.json()['aud']

        if audience == settings.GOOGLE_OAUTH2_CLIENT_ID:
            return True
        else:
            raise ValidationError('Invalid audience.')
    else:
        raise ValidationError('id_token is invalid.')


def request_gg_access_token(*, code: str, redirect_uri: str) -> str:
    # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#obtainingaccesstokens
    data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)

    if response.ok:
        access_token = response.json()['access_token']
        return access_token
    else:
        raise ValidationError(
            f'Failed to obtain access token from Google. Detail: {response.json()["error"]} - {response.json()["error_description"]}')


def request_gg_user_info(*, access_token: str) -> Dict[str, Any]:
    # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
    params = {'access_token': access_token}

    response = requests.get(GOOGLE_USER_INFO_URL, params=params)

    if response.ok:
        data = response.json()
        user_data = {
            'email': data['email'],
            'first_name': data.get('given_name', ''),
            'last_name': data.get('family_name', ''),
            # 'picture': data.get('picture', ''),
        }
        return user_data
    else:
        raise ValidationError(
            f'Failed to obtain user info from Google. Detail: {response.json()["error"]} - {response.json()["error_description"]}')


def request_fb_access_token(*, code: str, redirect_uri: str) -> str:
    # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#obtainingaccesstokens
    params = {
        'code': code,
        'client_id': settings.FACEBOOK_CLIENT_ID,
        'client_secret': settings.FACEBOOK_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
    }

    response = requests.get(FACEBOOK_ACCESS_TOKEN_OBTAIN_URL, params=params)

    if response.ok:
        print(response.json())
        access_token = response.json()['access_token']
        return access_token
    else:
        raise ValidationError(
            f'Failed to obtain access token from Facebook. Detail: {response.json()["error"]} - {response.json()["error_description"]}')


def request_fb_user_id(*, access_token: str) -> str:
    # Reference: https://developers.facebook.com/docs/graph-api/reference/v13.0/user
    params = {
        'access_token': access_token,
    }

    response = requests.get(f'{FACEBOOK_USER_ID_URL}', params=params)

    if response.ok:
        # print(response.json())
        user_id = response.json()['id']
        return user_id
    else:
        raise ValidationError(
            f'Failed to obtain user ID from Facebook. Detail: {response.json()["error"]}')


def request_fb_user_info(*, access_token: str, user_id: str) -> Dict[str, Any]:
    # Reference: https://developers.facebook.com/docs/graph-api/reference/v13.0/user
    params = {
        'fields': 'email,name,first_name,last_name,gender,birthday,picture',
        'access_token': access_token,
    }

    response = requests.get(
        f'{FACEBOOK_USER_INFO_URL}/{user_id}', params=params)

    if response.ok:
        # print(response.json())
        return response.json()
    else:
        raise ValidationError(
            f'Failed to obtain user info from Facebook. Detail: {response.json()["error"]}')


def get_or_create_user(*, data) -> Tuple[User, bool]:
    # create user if not exist
    is_create = False

    try:
        user = User.objects.get(email=data['email'])
    except User.DoesNotExist:
        is_create = True
        user = User()
        # Set random default password
        user.password = make_password(None)
        user.email = data['email']
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.save()

    return user, is_create


def jwt_login(*, user: User, get_token_func=RefreshToken.for_user) -> Dict[str, Any]:
    """
    Create JWT login from user obj
    Return user_data -> dict, contain token pair & user info 
    """
    # Blacklist old refresh token
    try:
        RefreshToken(user.refresh).blacklist()
    except TokenError:
        pass

    # Refresh token
    refresh = get_token_func(user)
    token_pair = {
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }

    # Update last_login & refresh field
    user.last_login = timezone.now()
    user.refresh = token_pair['refresh']
    user.save(update_fields=['last_login', 'refresh'])

    return token_pair
