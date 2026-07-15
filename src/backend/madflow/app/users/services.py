from django.contrib.auth import get_user_model

User = get_user_model()

def register_user(validated_data):
    password = validated_data.pop('password')
    user = User(**validated_data)
    user.set_password(password)
    user.save()
    return user

def get_all_users():
    return User.objects.all()