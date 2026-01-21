# PYInvest API (Backend) 🏦

API REST desenvolvida com **Django Rest Framework (DRF)** para gerenciar um sistema bancário simplificado. Este projeto atua como a fonte da verdade, gerenciando banco de dados, regras de negócio financeiras, autenticação e segurança.

## 🚀 Funcionalidades

- **Autenticação Customizada:**
  - Login com E-mail e Senha + Validação de CPF.
  - Cadastro transacional (Usuário + Dados Pessoais) com verificação de e-mail.
  - Recuperação e Troca de Senha/E-mail.
- **Gestão de Contas:**
  - Criação de Conta Corrente (Uma por CPF).
  - Soft Delete (Desativação de conta e usuário) com verificação de saldo.
- **Operações Financeiras:**
  - Depósito e Saque.
  - Cálculo de Score de Crédito (Lógica centralizada).
  - Histórico de Movimentações.
  - Sistema de investimentos
- **Segurança:**
  - Endpoints protegidos por Token Authentication.
  - Validação de integridade de dados (CPF único, saldo não negativo).

## 🛠️ Tecnologias

- Python 3.12+
- Django 5+
- Django Rest Framework
- Django Rest Authemail
- SQLite (Desenvolvimento)

## ⚙️ Instalação e Execução

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/TiagoBryan/py_investment_api.git
   cd py_investment_api
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurações de Ambiente (.env):**
   (Opcional) Configure `SECRET_KEY` e `DEBUG` no seu settings.py ou use variáveis de ambiente.
   Certifique-se de configurar o envio de e-mail (para dev, use o console backend):
   ```python
   # settings.py
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
   AUTH_EMAIL_VERIFICATION = True
   ```

5. **Execute as migrações:**
   ```bash
   python manage.py migrate
   ```

6. **Inicie o servidor:**
   ```bash
   python manage.py runserver 8000
   ```
   A API estará disponível em `http://127.0.0.1:8000/`.

## 🧪 Testes

O projeto possui cobertura de testes para Models, Serializers e Views (Endpoints).

```bash
python manage.py test
```

## 🔗 Principais Endpoints

| Método | Endpoint | Descrição |
| --- | --- | --- |
| POST | `/api/signup/cliente/` | Cadastro completo (User + Pessoa) |
| POST | `/api/login/custom/` | Login com validação de CPF |
| GET | `/api/contas/` | Dados da conta do usuário logado |
| POST | `/api/conta/deposito/` | Realizar depósito |
| POST | `/api/conta/saque/` | Realizar saque |
| POST | `/api/users/me/desativar/` | Soft Delete do usuário |

---