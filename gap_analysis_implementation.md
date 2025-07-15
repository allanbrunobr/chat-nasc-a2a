# Implementação de Análise de Gaps Candidato x Vaga

## 1. Conceito e Objetivo

### O que são gaps?
- **Skills Gaps**: Habilidades que a vaga exige mas o candidato não possui
- **Experience Gaps**: Diferença de tempo de experiência exigido vs possuído
- **Education Gaps**: Formação exigida que o candidato não tem
- **Certification Gaps**: Certificações específicas ausentes
- **Language Gaps**: Idiomas exigidos não dominados

### Objetivo:
Mostrar ao candidato exatamente o que falta para ele se qualificar melhor para uma vaga específica, com sugestões de como preencher essas lacunas.

## 2. Fluxo de Interação

### Comandos do usuário:
```
- "analisar gaps para vaga [ID]"
- "o que falta para eu me candidatar à vaga [ID]"
- "comparar meu perfil com a vaga [ID]"
- "requisitos que não atendo da vaga [ID]"
```

### Resposta esperada:
```markdown
📊 **Análise de Compatibilidade - Vaga: Desenvolvedor Senior Java**

✅ **Você atende**: 7 de 10 requisitos (70%)

❌ **Gaps identificados:**

**1. Experiência com Spring Boot**
   - Exigido: 3 anos
   - Seu perfil: Não identificado
   💡 Sugestão: Curso "Spring Boot Completo" na plataforma X

**2. Certificação AWS**
   - Exigido: AWS Certified Developer
   - Seu perfil: Não possui
   💡 Sugestão: Preparatório AWS Developer Associate

**3. Inglês Avançado**
   - Exigido: Fluente/Avançado
   - Seu perfil: Intermediário
   💡 Sugestão: Curso de Business English

📈 **Plano de Ação Recomendado:**
1. Priorize Spring Boot (impacto alto)
2. Melhore inglês (diferencial importante)
3. Considere certificação AWS (médio prazo)

🎯 Com essas melhorias, sua compatibilidade pode chegar a 95%!
```

## 3. Arquitetura Técnica

### 3.1 Nova Tool no ADK
```python
# nai/tools/analyze_gap.py
from google.adk.tools import FunctionTool, ToolContext
import requests
import logging

def analyze_gap(tool_context: ToolContext, vacancy_id: str) -> dict:
    """
    Analisa gaps entre perfil do candidato e vaga específica
    """
    user_id = get_user_id_from_context(tool_context)
    
    # Buscar dados da vaga
    vacancy_data = fetch_vacancy_details(vacancy_id)
    
    # Buscar perfil do candidato
    user_profile = fetch_user_profile(user_id)
    
    # Analisar gaps
    gaps = calculate_gaps(user_profile, vacancy_data)
    
    # Buscar sugestões de cursos/certificações
    suggestions = get_improvement_suggestions(gaps)
    
    return {
        "status": "success",
        "vacancy": vacancy_data,
        "gaps": gaps,
        "suggestions": suggestions,
        "compatibility_score": calculate_compatibility(user_profile, vacancy_data)
    }

analyze_gap_tool = FunctionTool(func=analyze_gap)
```

### 3.2 Endpoint no Backend
```typescript
// backend/src/modules/match/match.service.ts
async analyzeGaps(userId: string, vacancyId: string) {
    const userProfile = await this.getUserProfile(userId);
    const vacancy = await this.getVacancyDetails(vacancyId);
    
    const gaps = {
        skills: this.analyzeSkillGaps(userProfile.skills, vacancy.requirements),
        experience: this.analyzeExperienceGaps(userProfile.experiences, vacancy.minExperience),
        education: this.analyzeEducationGaps(userProfile.education, vacancy.requiredEducation),
        languages: this.analyzeLanguageGaps(userProfile.languages, vacancy.requiredLanguages),
        certifications: this.analyzeCertificationGaps(userProfile.certifications, vacancy.requiredCertifications)
    };
    
    return {
        gaps,
        suggestions: await this.getSuggestions(gaps),
        compatibilityScore: this.calculateScore(userProfile, vacancy)
    };
}
```

### 3.3 Algoritmo de Análise de Gaps

```python
def calculate_gaps(user_profile, vacancy):
    gaps = []
    
    # 1. Skills Gaps
    required_skills = set(vacancy.get('required_skills', []))
    user_skills = set([s['name'].lower() for s in user_profile.get('skills', [])])
    
    missing_skills = required_skills - user_skills
    for skill in missing_skills:
        gaps.append({
            'type': 'skill',
            'name': skill,
            'severity': 'high' if skill in vacancy.get('mandatory_skills', []) else 'medium',
            'description': f'Habilidade {skill} é exigida mas não consta no seu perfil'
        })
    
    # 2. Experience Gaps
    if vacancy.get('min_experience_years'):
        user_experience_years = calculate_total_experience(user_profile)
        if user_experience_years < vacancy['min_experience_years']:
            gaps.append({
                'type': 'experience',
                'required': vacancy['min_experience_years'],
                'current': user_experience_years,
                'severity': 'high',
                'description': f'Vaga exige {vacancy["min_experience_years"]} anos, você tem {user_experience_years}'
            })
    
    # 3. Education Gaps
    required_education = vacancy.get('education_level')
    user_education = get_highest_education(user_profile)
    if not meets_education_requirement(user_education, required_education):
        gaps.append({
            'type': 'education',
            'required': required_education,
            'current': user_education,
            'severity': 'medium',
            'description': f'Formação exigida: {required_education}'
        })
    
    return gaps
```

## 4. Integração com Prompt do NAI

### Adicionar ao prompt.py:
```python
ANALISE_GAP_INSTRUCOES = """
Quando o usuário pedir análise de gaps ou requisitos de uma vaga:

1. SEMPRE use analyze_gap_tool com o ID da vaga
2. Apresente os resultados de forma clara e motivadora
3. Estruture a resposta em:
   - Resumo de compatibilidade (positivo primeiro!)
   - Gaps organizados por prioridade
   - Sugestões práticas e alcançáveis
   - Plano de ação com timeline

4. Use emojis para tornar visual:
   ✅ Requisitos atendidos
   ❌ Gaps identificados
   💡 Sugestões
   📈 Plano de ação
   🎯 Meta de compatibilidade

5. Seja encorajador:
   - Enfatize o que o candidato JÁ tem
   - Mostre que gaps são oportunidades de crescimento
   - Sugira alternativas quando apropriado
"""
```

## 5. Melhorias Futuras

### 5.1 Gap Score Ponderado
```python
gap_weights = {
    'mandatory_skill': 1.0,
    'preferred_skill': 0.6,
    'experience': 0.8,
    'education': 0.7,
    'certification': 0.5,
    'language': 0.4
}

def calculate_weighted_gap_score(gaps, weights):
    total_weight = sum(weights.values())
    gap_impact = sum(gap['weight'] * weights.get(gap['type'], 0.5) for gap in gaps)
    return 100 - (gap_impact / total_weight * 100)
```

### 5.2 Sugestões Inteligentes
- Integrar com API de cursos online (Udemy, Coursera)
- Recomendar cursos gratuitos do SENAI/SETASC
- Priorizar por ROI (retorno sobre investimento de tempo)
- Considerar tempo disponível do candidato

### 5.3 Tracking de Progresso
```python
def track_gap_closure(user_id, gap_id):
    """
    Permite candidato marcar gaps como "em progresso" ou "concluído"
    """
    return {
        'gap_id': gap_id,
        'status': 'in_progress',
        'started_at': datetime.now(),
        'estimated_completion': calculate_estimated_time(gap_type)
    }
```

## 6. Exemplo de Implementação Completa

### Comando: "analisar gaps para vaga 123"

### Resposta do Sistema:
```markdown
📊 **Análise Detalhada - Desenvolvedor Full Stack Senior**

🎯 **Sua Compatibilidade Atual: 72%**

✅ **Você já possui:**
- ✓ JavaScript (5 anos)
- ✓ React.js (3 anos)
- ✓ Node.js (2 anos)
- ✓ Git/GitHub
- ✓ Metodologias Ágeis

❌ **Gaps Identificados (por prioridade):**

**1. 🔴 Docker & Kubernetes** (Alta prioridade)
   - Status: Não encontrado no seu perfil
   - Impacto: -15% na compatibilidade
   💡 **Ação recomendada**: 
      - Curso "Docker para Desenvolvedores" (20h)
      - Prática com projetos pessoais
      - Tempo estimado: 30 dias

**2. 🟡 AWS Cloud Services** (Média prioridade)
   - Status: Conhecimento básico vs Avançado exigido
   - Impacto: -8% na compatibilidade
   💡 **Ação recomendada**:
      - AWS Free Tier + Hands-on Labs
      - Certificação AWS Developer Associate
      - Tempo estimado: 60 dias

**3. 🟢 Inglês Técnico** (Baixa prioridade)
   - Status: Intermediário vs Fluente desejado
   - Impacto: -5% na compatibilidade
   💡 **Ação recomendada**:
      - Documentação técnica em inglês
      - Meetups internacionais online
      - Tempo estimado: Contínuo

📈 **Seu Plano de Ação Personalizado:**

**Próximos 30 dias:**
1. Iniciar curso de Docker (2h/dia)
2. Criar projeto pessoal com containers
3. Documentar aprendizado no GitHub

**30-60 dias:**
1. Começar estudos AWS
2. Deploy do projeto em AWS com Docker
3. Participar de comunidades DevOps

**60-90 dias:**
1. Preparação para certificação AWS
2. Contribuir com projetos open source
3. Atualizar perfil com novas skills

🚀 **Potencial após melhorias: 95% de compatibilidade!**

💬 Gostaria de:
- Ver cursos recomendados específicos?
- Analisar outra vaga?
- Criar um plano de estudos detalhado?
```

## 7. Benefícios da Implementação

1. **Para o Candidato:**
   - Clareza sobre o que melhorar
   - Plano de ação concreto
   - Motivação para desenvolvimento
   - Economia de tempo focando no essencial

2. **Para o Sistema:**
   - Maior engajamento dos usuários
   - Dados valiosos sobre gaps do mercado
   - Oportunidades de parcerias educacionais
   - Melhoria contínua dos matches

3. **Para Empresas:**
   - Candidatos mais preparados
   - Redução de gaps através de capacitação
   - Insights sobre escassez de talentos