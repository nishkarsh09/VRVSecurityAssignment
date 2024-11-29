from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Role
from .rbac import IsAdmin, IsModerator, IsUser
from django.http import HttpResponse

User = get_user_model()

# Home view with Postman collection link
def home(request):
    return HttpResponse('<h1><a href="https://documenter.getpostman.com/view/26432004/2sAYBVhXRH#08b29e5c-2396-47b0-b23c-274c1557d65d" target="_blank">Click to check Postman collection</a></h1>')

# User Registration View
class RegisterView(APIView):
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            role_name = request.data.get('role')
            
            role = Role.objects.get(name=role_name)
            user = User.objects.create_user(username=username, password=password, role=role)
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        except Role.DoesNotExist:
            return Response({"error": "Invalid role specified"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# User Login View
class LoginView(APIView):
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            user = User.objects.get(username=username)
            
            # Check if the account is locked
            if user.is_account_locked():
                return Response({"error": "Account is locked. Try again later."}, status=status.HTTP_403_FORBIDDEN)
            
            # Verify password
            if user.check_password(password):
                user.failed_attempts = 0  # Reset failed attempts on successful login
                user.lockout_until = None  # Clear lockout if applicable
                user.save()
                
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                })
            
            # Handle failed login attempt
            user.failed_attempts += 1
            if user.failed_attempts >= 5:  # Lock account after 5 failed attempts
                user.lockout_until = timezone.now() + timedelta(minutes=30)
                user.save()
                return Response({"error": "Account locked due to too many failed attempts."}, status=status.HTTP_403_FORBIDDEN)
            
            user.save()
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# User Logout View
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Blacklist refresh token
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Views restricted based on user roles
class AdminView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            return Response({"message": "Welcome Admin!"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModeratorView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]

    def get(self, request):
        try:
            return Response({"message": "Welcome Moderator!"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserView(APIView):
    permission_classes = [IsAuthenticated, IsUser]

    def get(self, request):
        try:
            return Response({"message": "Welcome User!"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)