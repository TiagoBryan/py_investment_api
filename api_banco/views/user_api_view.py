from django.contrib.auth import get_user_model
from rest_framework.authentication import SessionAuthentication, \
    BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _


from rest_framework import status
from api_banco.serializers import (MyUserSerializer,
                                   MyUserChangeSerializer,)


from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from api_banco.serializers import UserDeactivateSerializer


User = get_user_model()


class AuthenticationView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        content = {
            'user': str(request.user),  # `django.contrib.auth.User` instance.
            'auth': str(request.auth),  # None
        }
        return Response(content)


class MyUserMe(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyUserSerializer

    def get(self, request, format=None):
        return Response(self.serializer_class(request.user).data)


class MyUserMeChange(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyUserChangeSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = request.user

            if 'first_name' in serializer.data:
                user.first_name = dict(serializer.data)['first_name']
            if 'last_name' in serializer.data:
                user.last_name = dict(serializer.data)['last_name']

            user.save()

            content = {'success': _('User information changed.')}
            return Response(content, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserDeactivateSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if hasattr(user, 'pessoa') and hasattr(user.pessoa, 'conta_corrente'):
            conta = user.pessoa.conta_corrente
            if conta.saldo != 0:
                return Response(
                    {"detail": "Não é possível excluir o usuário pois "
                     "há saldo na conta corrente. Zere o saldo primeiro."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if hasattr(user.pessoa, 'perfil_investidor'):
            tem_investimentos = user.pessoa.perfil_investidor\
                                    .investimentos.filter(ativo=True).exists()
            if tem_investimentos:
                return Response(
                    {"detail": "Não é possível excluir o usuário pois há \
                    investimentos ativos. Resgate seus ativos primeiro."},
                    status=status.HTTP_400_BAD_REQUEST
                    )

        try:
            with transaction.atomic():
                user.is_active = False
                user.save()

                if hasattr(user, 'pessoa') and hasattr(user.pessoa,
                                                       'conta_corrente'):
                    conta = user.pessoa.conta_corrente
                    conta.ativa = False
                    conta.save()

                send_mail(
                    subject='Sua conta foi desativada',
                    message=f"Olá {user.first_name},\n\nSeu usuário e "
                            "sua conta bancária foram desativados com "
                            "sucesso.\nEsperamos vê-lo novamente em breve.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

                request.auth.delete()

            return Response(
                {"detail": "Usuário desativado com sucesso."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"detail": f"Erro ao desativar usuário: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
