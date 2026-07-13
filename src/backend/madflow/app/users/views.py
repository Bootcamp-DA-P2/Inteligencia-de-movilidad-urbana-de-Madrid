from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate, login
from .services import get_all_users
from .serializers import RegisterSerializer, UserListSerializer

User = get_user_model()

class UserListView(APIView):
    # Validamos usando la sesión tradicional del navegador/cliente en lugar de un token JWT
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "No autorizado. Inicia sesión primero."}, status=status.HTTP_401_UNAUTHORIZED)
            
        users = get_all_users()
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [] 

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Usuario creado con éxito",
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email y contraseña son requeridos"}, status=status.HTTP_400_BAD_REQUEST)

        # Autenticamos contra la base de datos (Django usa tu USERNAME_FIELD = 'email')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user) # Crea la sesión activa en el backend
            return Response({
                "message": "Login correcto",
                "user": {
                    "email": user.email,
                    "name": user.name,
                    "surname": user.surname
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)