from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class RegisterView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		username = (request.data.get('username') or '').strip()
		email = (request.data.get('email') or '').strip()
		password = request.data.get('password') or ''

		if not username or not password:
			return Response({'error': 'username va password la bat buoc.'}, status=status.HTTP_400_BAD_REQUEST)

		if User.objects.filter(username=username).exists():
			return Response({'error': 'username da ton tai.'}, status=status.HTTP_400_BAD_REQUEST)

		user = User.objects.create_user(
			username=username,
			email=email,
			password=password,
		)
		return Response({'id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)
