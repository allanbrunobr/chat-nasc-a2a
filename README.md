# NASC - Assistente Virtual Inteligente do SETASC

Este projeto implementa a NASC (Núcleo de Assistência Smart para Carreira), a assistente virtual inteligente do SETASC. A plataforma auxilia usuários em sua jornada profissional, oferecendo criação e gestão de perfis profissionais, matching inteligente com vagas, análise de gaps de competências e recomendações personalizadas de desenvolvimento de carreira.

## 🚀 Funcionalidades Principais

- **Gestão de Perfil Profissional**: Criação e edição de currículos através de múltiplas modalidades (PDF, áudio, vídeo, texto)
- **Matching Inteligente**: Análise de compatibilidade entre perfil do usuário e vagas disponíveis
- **Análise de Gaps**: Identificação de lacunas de competências para transições de carreira
- **Recomendações Personalizadas**: Sugestões de cursos e trilhas de desenvolvimento
- **Interface Conversacional**: Interação natural via chat com a assistente NASC

## 🛠️ Tecnologias Utilizadas

- **Backend**: FastAPI (Python)
- **IA**: Google Gemini 2.0 Flash + Agent Development Kit (ADK)
- **Banco de Dados**: PostgreSQL (Cloud SQL)
- **Infraestrutura**: Google Cloud Run
- **Autenticação**: Service Account + API Keys

## 📁 Estrutura do Projeto

```text
nai-api/
├── api/                          # Backend FastAPI
│   ├── main.py                   # Endpoint principal /run
│   └── utils/                    # Utilitários
│       ├── gemini.py             # Extração de conteúdo de arquivos
│       └── gemini_update_profile.py  # Enriquecimento de perfil
│
├── nai/                          # Núcleo NASC com ADK
│   ├── agent.py                  # Agente principal
│   ├── prompt.py                 # Instruções do agente
│   └── tools/                    # Ferramentas do agente
│       ├── retrieve_user_info.py # Recuperar perfil
│       ├── save_user_profile.py  # Salvar perfil
│       ├── update_state.py       # Atualizar estado
│       ├── retrieve_match.py     # Buscar matches
│       └── retrieve_vacancy.py   # Buscar vagas
│
├── test/                         # Testes e frontend demo
│   └── front/                    
│       └── index.html            # Interface web de teste
│
├── docs/                         # Documentação e cloud functions
├── .env                          # Variáveis de ambiente
├── requirements.txt              # Dependências Python
├── Dockerfile                    # Container para deploy
└── README.md                     # Este arquivo
```

## 🔧 Configuração do Ambiente

### 1. Pré-requisitos

- Python 3.9+
- PostgreSQL
- Conta Google Cloud com APIs habilitadas
- Credenciais de serviço SETASC

### 2. Variáveis de Ambiente (.env)

```env
# Google AI
GOOGLE_API_KEY=sua_api_key_aqui
GOOGLE_GENAI_USE_VERTEXAI=False

# URLs dos Serviços SETASC
USER_PROFILE_URL=https://...
RETRIEVE_MATCH_URL=https://...
RETRIEVE_GAP_URL=https://...
RETRIEVE_VACANCY_URL=https://...
RETRIEVE_CAPACITY_FUNCTION_URL=https://...

# Banco de Dados PostgreSQL
DB_HOST=seu_host
DB_PORT=5432
DB_NAME=vcc-db-v2
DB_USER=postgres
DB_PASSWORD=sua_senha

# Credenciais
SERVICE_ACCOUNT_PATH=nai/nai-setasc-credentials.json
```

### 3. Instalação Local

```bash
# Clonar o repositório
git clone [url-do-repositorio]
cd nai-api

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Executar aplicação
uvicorn api.main:app --reload --port 8080
```

## 🐳 Docker

### Build e Execução Local

```bash
# Build da imagem
docker build -t nasc-api .

# Executar container
docker run -p 8080:8080 --env-file .env nasc-api
```

### Deploy no Google Cloud Run

```bash
# Tag da imagem para Artifact Registry
docker tag nasc-api southamerica-east1-docker.pkg.dev/setasc-central-emp-dev/nasc/nasc-api:latest

# Push para Artifact Registry
docker push southamerica-east1-docker.pkg.dev/setasc-central-emp-dev/nasc/nasc-api:latest

# Deploy no Cloud Run
gcloud run deploy nasc-api \
  --image southamerica-east1-docker.pkg.dev/setasc-central-emp-dev/nasc/nasc-api:latest \
  --platform managed \
  --region southamerica-east1 \
  --set-env-vars $(grep -v '^#' .env | xargs | sed 's/ /,/g')
```

## 🧪 Testando a Aplicação

### Interface Web de Teste

1. Abra `test/front/index.html` no navegador
2. Configure o User ID e Session ID
3. Interaja com a NASC através do chat

### Chamada direta à API

```bash
# Enviar mensagem de texto
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "seu-user-id",
    "session_id": "session-123",
    "message": "Olá"
  }'

# Enviar arquivo (multipart)
curl -X POST http://localhost:8080/run \
  -F "user_id=seu-user-id" \
  -F "session_id=session-123" \
  -F "file=@curriculum.pdf" \
  -F "message=Aqui está meu currículo"
```

## 📊 Fluxos de Conversação

### 1. Criação de Perfil
- Opções: PDF, áudio, vídeo, papo estruturado, texto livre
- Validação automática de campos obrigatórios
- Conversação guiada para completar informações

### 2. Busca de Vagas
- Vagas alinhadas ao perfil (matching)
- Busca por localização ou área específica
- Apresentação com percentual de compatibilidade

### 3. Análise de Gaps
- Identificação de competências faltantes
- Sugestões de desenvolvimento
- Recomendação de cursos SETASC

## 🔒 Segurança

- Autenticação via Service Account
- Isolamento de dados por usuário
- Sem armazenamento de dados sensíveis
- CORS configurável

## 📝 Logs e Monitoramento

Os logs são estruturados e incluem:
- Requisições recebidas
- Interações com o agente
- Chamadas às ferramentas
- Erros e exceções

Para monitoramento em produção, integre com Google Cloud Logging e Monitoring.

## 🤝 Contribuindo

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é propriedade do SETASC e está sob licença proprietária.

## 🆘 Suporte

Para suporte e dúvidas:
- Documentação técnica: `docs/TECHNICAL_DOCUMENTATION.md`
- Issues: [Sistema de Issues do projeto]
- Contato: [equipe-desenvolvimento@setasc.mt.gov.br]

---

**NASC** - Transformando carreiras através da inteligência artificial 🚀