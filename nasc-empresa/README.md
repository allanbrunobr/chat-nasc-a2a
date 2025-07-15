# NASC-E - Chat Empresarial do SETASC

Assistente virtual inteligente para empresas gerenciarem vagas e processos de recrutamento na plataforma SETASC.

## 🚀 Funcionalidades

### 1. Gestão de Vagas
- Criar novas vagas com todos os detalhes
- Editar vagas existentes
- Ativar/desativar vagas
- Listar todas as vagas da empresa

### 2. Análise de Compatibilidade
- Buscar candidatos compatíveis por vaga
- Ver score de match (0-100%)
- Analisar score ATS dos candidatos
- Filtrar por localização, experiência e competências

### 3. Gestão de Candidaturas
- Listar candidatos que se aplicaram
- Atualizar status (novo, em análise, entrevista, aprovado, rejeitado)
- Adicionar feedback e observações
- Ver perfil completo dos candidatos

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL
- Google API Key (Gemini)
- Backend SETASC rodando na porta 3030

## 🔧 Instalação

1. Clone o repositório e acesse a pasta:
```bash
cd nasc-empresa
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env`:
```bash
cp .env.example .env
# Edite o arquivo com suas credenciais
```

## ⚙️ Configuração

### Variáveis de Ambiente Importantes:

- `GOOGLE_API_KEY`: Chave da API do Google Gemini
- `DB_*`: Configurações do banco de dados PostgreSQL
- `BACKEND_URL`: URL do backend SETASC (padrão: http://localhost:3030)
- `JWT_SECRET`: Segredo para validação de tokens JWT
- `EMPRESA_API_PORT`: Porta do servidor (padrão: 8081)

## 🏃‍♂️ Executando

### Iniciar o servidor:
```bash
python start_server.py
```

O servidor estará disponível em:
- API: http://localhost:8081
- Documentação: http://localhost:8081/docs

### Executar testes:
```bash
python test_empresa.py
```

## 📡 Endpoints Principais

### Chat Principal
```
POST /run
Authorization: Bearer {jwt_token}

{
  "user_id": "empresa_id",
  "message": "Quero criar uma nova vaga",
  "session_id": "opcional"
}
```

### Criar Vaga Diretamente
```
POST /vacancy/create
Authorization: Bearer {jwt_token}

{
  "title": "Desenvolvedor Full Stack",
  "position": "Desenvolvedor",
  "description": "Descrição da vaga",
  "location": "Cuiabá/MT",
  ...
}
```

### Buscar Matches
```
GET /vacancy/{vacancy_id}/matches?min_score=70&limit=20
Authorization: Bearer {jwt_token}
```

## 🔒 Autenticação

O sistema valida que o usuário tem `role=EMPRESA` através do token JWT. Tokens sem essa role receberão erro 403.

## 🛠️ Estrutura do Projeto

```
nasc-empresa/
├── api/
│   ├── main.py          # API FastAPI principal
│   └── utils/           # Utilidades
├── nasc_e/              # Core do agente
│   ├── agent.py         # Configuração do agente
│   ├── prompt.py        # Instruções da NASC-E
│   └── tools/           # Ferramentas
│       ├── retrieve_company_info.py
│       ├── manage_vacancy.py
│       ├── retrieve_matches.py
│       └── retrieve_applicants.py
├── .env                 # Configurações
├── requirements.txt     # Dependências
├── start_server.py      # Script de inicialização
└── test_empresa.py      # Testes
```

## 📝 Exemplos de Uso

### Conversação Típica:
```
Empresa: "Olá"
NASC-E: "Olá! Sou a NASC-E, sua assistente para gestão de vagas..."

Empresa: "Quero criar uma vaga de desenvolvedor"
NASC-E: "Ótimo! Vamos começar. Qual o título do cargo?"

Empresa: "Desenvolvedor Backend Pleno"
NASC-E: "Excelente! Agora preciso de uma descrição das responsabilidades..."
```

## 🐛 Solução de Problemas

### Erro de autenticação:
- Verifique se o token JWT tem role=EMPRESA
- Confirme que JWT_SECRET está correto

### Timeout nas APIs:
- Verifique se o backend está rodando
- Confirme as URLs no .env

### Erro ao conectar banco:
- Verifique credenciais PostgreSQL
- Confirme que o banco está acessível

## 📚 Documentação Adicional

- API Docs: http://localhost:8081/docs
- Swagger UI: http://localhost:8081/redoc
- Logs: Configure LOG_LEVEL no .env

## 🤝 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento do SETASC.