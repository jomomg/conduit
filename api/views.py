from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from api.serializers import UserProfileSerializer, LoginSerializer


class UserRegistration(APIView):
    """
    View for registering a user
    """
    permission_classes = []

    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'user': serializer.data}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class UserLogin(APIView):
    """
    View for loging in a user
    """
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            response = {'user': serializer.data}
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class SingleUser(APIView):
    def get(self, request):
        pass

    def put(self, request):
        pass
