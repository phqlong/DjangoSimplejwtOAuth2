from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainSerializer

from users.models import User
from users.services import jwt_login


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name',
                  'last_login', 'is_staff']

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.password = validated_data.get('password', instance.password)
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.email)
        instance.refresh = validated_data.get('refresh', instance.refresh)
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs):
        '''Return data contain User info and token pair'''
        # Validate user by email and password
        super().validate(attrs)

        # Get JWT and user info
        token_pair = jwt_login(user=self.user, get_token_func=self.get_token)

        # Get user_data and Add to token_pair
        serializer = UserSerializer(self.user, many=False)
        user_data = {key: val for (key, val) in serializer.data.items()}
        user_data = {**user_data, **token_pair}

        return user_data
