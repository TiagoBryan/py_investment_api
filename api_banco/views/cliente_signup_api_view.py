from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth import get_user_model
from ipware import get_client_ip

from authemail.models import SignupCode
from api_banco.serializers import (ClienteSignupSerializer,
                                   CustomLoginSerializer,)
from api_banco.models import Pessoa

from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny


class ClienteSignupAPIView(APIView):
    permission_classes = []

    def post(self, request):

        serializer = ClienteSignupSerializer(data=request.data)

        if serializer.is_valid():

            data = serializer.validated_data
            try:
                with transaction.atomic():

                    User = get_user_model()

                    user = User.objects.create_user(
                        email=data['email'],  # type: ignore
                        password=data['password'],  # type: ignore
                        first_name=data['first_name'],  # type: ignore
                        last_name=data['last_name']  # type: ignore
                    )

                    user.is_verified = False  # type: ignore
                    user.save()

                    first_name = data['first_name']  # type: ignore
                    last_name = data['last_name']  # type: ignore

                    Pessoa.objects.create(
                        user=user,
                        tipo_pessoa=data['tipo_pessoa'],  # type: ignore
                        cpf_cnpj=data['cpf_cnpj'],  # type: ignore
                        nome=f"{first_name} {last_name}",
                        confirmado=False
                    )

                    client_ip = get_client_ip(request)[0]
                    if client_ip is None:
                        client_ip = '0.0.0.0'

                    signup_code = SignupCode.objects.\
                        create_signup_code(user, client_ip)  # type: ignore

                    signup_code.send_signup_email()

                return Response(
                    {"detail": "Cadastro realizado. Verifique seu e-mail."},
                    status=status.HTTP_201_CREATED
                )

            except Exception:
                return Response(
                    {"detail": "Erro interno ao criar conta."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = CustomLoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = serializer.validated_data['user']  # type: ignore

            # Gera ou recupera o token
            token, created = Token.objects.get_or_create(user=user)

            return Response(
                {'token': token.key},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
