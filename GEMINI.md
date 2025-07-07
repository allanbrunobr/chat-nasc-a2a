# GEMINI.md - Resumo do Projeto NASC

Este arquivo contém um resumo de alto nível do projeto NASC (Núcleo de Assistência Smart para Carreira), a assistente virtual inteligente do SETASC, para ser usado como memória pelo Gemini.

## 🚀 Visão Geral do Projeto

O projeto implementa a NASC, uma assistente virtual para auxiliar usuários em sua jornada profissional. As principais funcionalidades incluem:

- **Gestão de Perfil Profissional**: Criação e edição de currículos via PDF, áudio, vídeo, ou texto.
- **Matching Inteligente**: Análise de compatibilidade entre o perfil do usuário e as vagas de emprego.
- **Análise de Gaps**: Identificação de lacunas de competências.
- **Recomendações Personalizadas**: Sugestões de cursos e trilhas de desenvolvimento.

## 🛠️ Arquitetura e Tecnologias

- **Backend**: FastAPI (Python)
- **IA**: Google Gemini 2.0 Flash + Agent Development Kit (ADK)
- **Banco de Dados**: PostgreSQL (Cloud SQL) com Prisma como ORM.
- **Infraestrutura**: Google Cloud Run
- **CI/CD**: Azure Pipelines

## 📁 Estrutura de Arquivos Essenciais

- `api/main.py`: Ponto de entrada da API FastAPI. Expõe o endpoint `/run` para interagir com o agente e `/enrich-profile` para enriquecer o perfil do usuário.
- `nai/agent.py`: Define o agente principal (`root_agent`) do ADK, que orquestra a conversa e o uso das ferramentas.
- `nai/prompt.py`: Contém o prompt principal (`ROOT_AGENT_INSTR`) que instrui o agente NASC sobre sua identidade, propósito, e regras de operação.
- `nai/tools/`: Diretório com as ferramentas que o agente pode utilizar.
    - `retrieve_user_info.py`: Busca informações do perfil do usuário.
    - `save_user_profile.py`: Salva o perfil do usuário.
    - `update_state.py`: Atualiza o estado do perfil na memória da conversa.
    - `retrieve_vacancy.py`: Busca por vagas de emprego.
    - `retrieve_match.py`: Realiza o matching entre o perfil e as vagas.
- `schema.prisma`: Define o schema do banco de dados PostgreSQL.
- `Dockerfile`: Configuração para containerizar a aplicação para deploy.
- `azure-pipelines.yml`: Define o pipeline de CI/CD para build e deploy no Google Cloud Run.
- `requirements.txt`: Lista de dependências Python do projeto.

## 🧠 Lógica Central e Fluxos

1.  **Início da Conversa**: Toda interação começa com a ferramenta `retrieve_user_info()` para carregar o perfil do usuário.
2.  **Criação/Edição de Perfil**:
    - O usuário pode fornecer informações via texto, PDF, áudio ou vídeo.
    - O conteúdo de arquivos não-textuais é extraído pela função `gemini_extract_text_from_file` em `api/utils/gemini.py`.
    - Todas as atualizações no perfil durante a conversa são feitas através da ferramenta `update_state_tool`, que usa o Gemini para interpretar a entrada do usuário e atualizar um JSON do perfil no estado da conversa.
    - A ferramenta `update_state` é instruída a realizar mapeamentos de termos em português para os enums em inglês definidos no `schema.prisma` (ex: "CLT" -> "EMPLOYEE").
3.  **Persistência**: O perfil completo é salvo no banco de dados apenas quando a ferramenta `save_user_profile()` é chamada.
4.  **Busca de Vagas**: A ferramenta `retrieve_vacancy` é usada para buscas semânticas, e a `retrieve_match` para encontrar vagas com maior compatibilidade com o perfil do usuário.

## 🔑 Pontos Importantes

- **Jacobi Iteration**: O prompt do agente (`nai/prompt.py`) instrui o modelo a usar uma estratégia chamada "Jacobi Iteration", que consiste em validar todos os campos do perfil em paralelo e solicitar todas as informações faltantes de uma só vez para otimizar o preenchimento do currículo.
- **Mapeamento de Dados**: Existe uma lógica forte de mapeamento de termos em português (usados na interação com o usuário) para os valores em inglês armazenados no banco de dados (definidos no `schema.prisma`). Essa conversão é uma responsabilidade do `update_state_tool`.
- **Estado da Conversa**: O estado da conversa (`tool_context.state`) é crucial, especialmente o objeto `perfil_profissional`, que armazena a versão mais recente do perfil do usuário antes de ser salvo permanentemente.
- **CI/CD**: O deploy é automatizado via Azure Pipelines, que realiza o build da imagem Docker e o deploy no Google Cloud Run.