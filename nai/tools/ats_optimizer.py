"""
ATS Optimizer - Funções para otimização de currículos para Applicant Tracking Systems

Este módulo contém funções para:
- Extrair palavras-chave de descrições de vagas
- Analisar perfis para compatibilidade ATS
- Sugerir otimizações
- Gerar versões otimizadas de currículos
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple
from collections import Counter
from datetime import datetime

logger = logging.getLogger(__name__)

# Palavras de ação recomendadas para ATS (por categoria)
ACTION_VERBS = {
    "lideranca": [
        "Liderou", "Gerenciou", "Coordenou", "Supervisionou", "Orientou",
        "Direcionou", "Comandou", "Delegou", "Motivou", "Treinou"
    ],
    "tecnico": [
        "Desenvolvi", "Desenvolveu", "Implementei", "Implementou", "Programei", "Programou", 
        "Configurei", "Configurou", "Otimizei", "Otimizou", "Automatizei", "Automatizou", 
        "Integrei", "Integrou", "Migrei", "Migrou", "Debuguei", "Debugou", "Testei", "Testou"
    ],
    "analise": [
        "Analisou", "Avaliou", "Examinou", "Investigou", "Identificou",
        "Diagnosticou", "Mapeou", "Estudou", "Pesquisou", "Interpretou"
    ],
    "melhoria": [
        "Melhorou", "Aumentou", "Reduziu", "Economizou", "Acelerou",
        "Simplificou", "Padronizou", "Modernizou", "Reestruturou", "Aperfeiçoou"
    ],
    "criacao": [
        "Criou", "Projetou", "Elaborou", "Concebeu", "Produziu",
        "Construiu", "Estabeleceu", "Fundou", "Iniciou", "Lançou"
    ],
    "comunicacao": [
        "Apresentou", "Comunicou", "Negociou", "Articulou", "Documentou",
        "Reportou", "Facilitou", "Mediou", "Colaborou", "Consultou"
    ]
}

# Termos problemáticos para ATS e suas substituições
PROBLEMATIC_TERMS = {
    # Abreviações comuns
    "JS": "JavaScript",
    "TS": "TypeScript", 
    "Py": "Python",
    "RH": "Recursos Humanos",
    "TI": "Tecnologia da Informação",
    "BI": "Business Intelligence",
    "UX": "User Experience",
    "UI": "User Interface",
    "API": "Application Programming Interface",
    "DB": "Database",
    "SQL": "Structured Query Language",
    
    # Termos informais
    "app": "aplicação",
    "apps": "aplicações",
    "dev": "desenvolvedor",
    "devs": "desenvolvedores",
    "tech": "tecnologia",
    "soft": "software",
    
    # Jargões que devem ser expandidos
    "CRUD": "Create, Read, Update, Delete",
    "POC": "Proof of Concept",
    "MVP": "Minimum Viable Product",
    "KPI": "Key Performance Indicator",
    "ROI": "Return on Investment"
}

# Formatos de data aceitos por ATS
DATE_FORMATS = {
    "ideal": "MM/AAAA",
    "aceitavel": ["MM/AAAA", "Mês AAAA", "AAAA"],
    "evitar": ["DD/MM/AAAA", "Mês de AAAA", "Apenas ano"]
}

# Seções essenciais de um currículo ATS-friendly
ESSENTIAL_SECTIONS = [
    "dados_pessoais",
    "resumo_profissional", 
    "experiencias",
    "formacao",
    "habilidades"
]

# Palavras-chave por área/indústria
INDUSTRY_KEYWORDS = {
    "tecnologia": [
        "desenvolvimento", "programação", "software", "sistemas", "aplicações",
        "backend", "frontend", "fullstack", "API", "REST", "microserviços",
        "cloud", "DevOps", "CI/CD", "agile", "scrum", "código", "algoritmos"
    ],
    "vendas": [
        "vendas", "metas", "clientes", "negociação", "prospecção",
        "relacionamento", "CRM", "pipeline", "conversão", "faturamento",
        "B2B", "B2C", "inside sales", "field sales", "consultivo"
    ],
    "administrativo": [
        "administração", "gestão", "processos", "documentação", "organização",
        "controle", "rotinas", "procedimentos", "relatórios", "planilhas",
        "atendimento", "secretariado", "arquivo", "agenda", "correspondência"
    ],
    "recursos_humanos": [
        "recursos humanos", "RH", "gestão de pessoas", "recrutamento", "seleção",
        "treinamento", "desenvolvimento", "folha de pagamento", "benefícios",
        "cultura organizacional", "clima", "performance", "onboarding", "employer branding"
    ],
    "marketing": [
        "marketing", "digital", "campanhas", "branding", "conteúdo",
        "SEO", "SEM", "redes sociais", "métricas", "KPIs", "ROI",
        "leads", "conversão", "funil", "persona", "estratégia"
    ]
}


def extract_keywords_from_text(text: str, min_length: int = 3) -> List[str]:
    """
    Extrai palavras-chave relevantes de um texto.
    
    Args:
        text: Texto para extrair palavras-chave
        min_length: Comprimento mínimo das palavras
        
    Returns:
        Lista de palavras-chave únicas
    """
    if not text:
        return []
    
    # Remove pontuação e converte para minúsculas
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Palavras a ignorar (stop words)
    stop_words = {
        'a', 'o', 'e', 'de', 'da', 'do', 'em', 'um', 'uma', 'para', 'com',
        'por', 'que', 'no', 'na', 'os', 'as', 'dos', 'das', 'ao', 'ou',
        'se', 'mas', 'mais', 'como', 'foi', 'são', 'será', 'ter', 'tem',
        'tinha', 'sido', 'já', 'quando', 'muito', 'nos', 'já', 'eu', 'seu'
    }
    
    # Extrai palavras
    words = text.split()
    keywords = []
    
    for word in words:
        if len(word) >= min_length and word not in stop_words:
            # Verifica se não é apenas números
            if not word.isdigit():
                keywords.append(word)
    
    # Remove duplicatas mantendo ordem
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords


def analyze_job_description(job_description: str) -> Dict[str, Any]:
    """
    Analisa uma descrição de vaga para extrair requisitos e palavras-chave.
    
    Args:
        job_description: Texto da descrição da vaga
        
    Returns:
        Dicionário com análise da vaga
    """
    analysis = {
        "keywords": [],
        "skills": [],
        "requirements": [],
        "nice_to_have": [],
        "action_verbs": []
    }
    
    # Extrai palavras-chave gerais
    analysis["keywords"] = extract_keywords_from_text(job_description)
    
    # Identifica seções comuns
    sections = {
        "requisitos": r"(?:requisitos|exigências|necessário|obrigatório)[\s:]*([^\.]+)",
        "desejavel": r"(?:desejável|diferencial|plus|nice to have)[\s:]*([^\.]+)",
        "responsabilidades": r"(?:responsabilidades|atividades|atribuições)[\s:]*([^\.]+)",
        "habilidades": r"(?:habilidades|competências|skills)[\s:]*([^\.]+)"
    }
    
    for section, pattern in sections.items():
        matches = re.finditer(pattern, job_description, re.IGNORECASE)
        for match in matches:
            content = match.group(1)
            keywords = extract_keywords_from_text(content)
            
            if section == "requisitos":
                analysis["requirements"].extend(keywords)
            elif section == "desejavel":
                analysis["nice_to_have"].extend(keywords)
            elif section == "habilidades":
                analysis["skills"].extend(keywords)
    
    # Identifica verbos de ação na descrição
    for category, verbs in ACTION_VERBS.items():
        for verb in verbs:
            if verb.lower() in job_description.lower():
                analysis["action_verbs"].append(verb)
    
    # Remove duplicatas
    for key in analysis:
        if isinstance(analysis[key], list):
            analysis[key] = list(set(analysis[key]))
    
    return analysis


def calculate_ats_score(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula o score ATS do perfil (0-100).
    
    Args:
        user_profile: Perfil do usuário
        
    Returns:
        Dicionário com score e análise detalhada
    """
    score = 0
    max_score = 100
    issues = []
    section_scores = {}
    
    # 1. Informações de contato (10 pontos)
    contact_score = 0
    if user_profile.get("email"):
        contact_score += 4
    else:
        issues.append("Email não informado")
        
    if user_profile.get("phone"):
        contact_score += 3
    else:
        issues.append("Telefone não informado")
        
    if user_profile.get("city") and user_profile.get("state"):
        contact_score += 3
    else:
        issues.append("Localização incompleta")
    
    section_scores["contact"] = contact_score
    score += contact_score
    
    # 2. Resumo profissional (15 pontos)
    summary_score = 0
    if user_profile.get("professionalSummary") or user_profile.get("visao_atual"):
        summary_text = user_profile.get("professionalSummary") or user_profile.get("visao_atual", "")
        if len(summary_text) > 50:
            summary_score += 10
            # Verifica se contém palavras-chave
            keywords = extract_keywords_from_text(summary_text)
            if len(keywords) > 5:
                summary_score += 5
        else:
            summary_score += 5
            issues.append("Resumo profissional muito curto")
    else:
        issues.append("Resumo profissional não encontrado")
    
    section_scores["summary"] = summary_score
    score += summary_score
    
    # 3. Experiências profissionais (25 pontos)
    experience_score = 0
    experiences = user_profile.get("experiences", [])
    
    if experiences:
        experience_score += 10
        
        # Verifica formatação de datas
        valid_dates = 0
        for exp in experiences:
            if exp.get("startDate") and re.match(r'\d{4}-\d{2}', exp["startDate"]):
                valid_dates += 1
        
        if valid_dates == len(experiences):
            experience_score += 5
        else:
            issues.append("Algumas experiências têm datas em formato incorreto")
        
        # Verifica uso de verbos de ação
        action_verb_count = 0
        for exp in experiences:
            activity = exp.get("activity", "")
            for verbs in ACTION_VERBS.values():
                for verb in verbs:
                    if verb.lower() in activity.lower():
                        action_verb_count += 1
                        break
        
        if action_verb_count >= len(experiences) * 0.7:
            experience_score += 5
        else:
            issues.append("Poucas experiências começam com verbos de ação")
        
        # Verifica se há conquistas quantificadas
        quantified_achievements = 0
        for exp in experiences:
            activity = exp.get("activity", "")
            # Procura por números, percentuais, valores monetários
            if re.search(r'\d+%|\$\d+|R\$\s*\d+|\d+\s*(?:mil|milhões)', activity):
                quantified_achievements += 1
        
        if quantified_achievements > 0:
            experience_score += 5
        else:
            issues.append("Adicione conquistas quantificadas às experiências")
    else:
        issues.append("Nenhuma experiência profissional cadastrada")
    
    section_scores["experience"] = experience_score
    score += experience_score
    
    # 4. Formação acadêmica (10 pontos)
    education_score = 0
    education = user_profile.get("education", [])
    
    if education:
        education_score += 7
        # Verifica campos completos
        complete_education = all(
            ed.get("institution") and ed.get("course") and ed.get("startDate")
            for ed in education
        )
        if complete_education:
            education_score += 3
        else:
            issues.append("Informações de formação incompletas")
    else:
        issues.append("Formação acadêmica não informada")
    
    section_scores["education"] = education_score
    score += education_score
    
    # 5. Habilidades (15 pontos)
    skills_score = 0
    hard_skills = user_profile.get("hardSkills", [])
    soft_skills = user_profile.get("softSkills", [])
    
    if hard_skills:
        skills_score += 7
        if len(hard_skills) >= 5:
            skills_score += 3
    else:
        issues.append("Nenhuma habilidade técnica cadastrada")
    
    if soft_skills:
        skills_score += 3
        if len(soft_skills) >= 3:
            skills_score += 2
    else:
        issues.append("Nenhuma habilidade comportamental cadastrada")
    
    section_scores["skills"] = skills_score
    score += skills_score
    
    # 6. Formatação e termos problemáticos (15 pontos)
    formatting_score = 15
    
    # Verifica termos problemáticos
    profile_text = str(user_profile)
    for problematic, replacement in PROBLEMATIC_TERMS.items():
        if problematic in profile_text:
            formatting_score -= 1
            issues.append(f"Substitua '{problematic}' por '{replacement}'")
    
    # Verifica formato de datas
    if experiences:
        for exp in experiences:
            start_date = exp.get("startDate", "")
            if start_date and not re.match(r'\d{4}-\d{2}', start_date):
                formatting_score -= 1
                issues.append("Use formato MM/AAAA para datas")
                break
    
    section_scores["formatting"] = max(0, formatting_score)
    score += max(0, formatting_score)
    
    # 7. Palavras-chave relevantes (10 pontos)
    keyword_score = 0
    
    # Extrai todas as palavras do perfil
    profile_keywords = set()
    for field in ["visao_atual", "visao_futuro"]:
        if user_profile.get(field):
            profile_keywords.update(extract_keywords_from_text(user_profile[field]))
    
    for exp in experiences:
        if exp.get("activity"):
            profile_keywords.update(extract_keywords_from_text(exp["activity"]))
    
    # Verifica presença de palavras-chave por indústria
    detected_industry = detect_user_industry(user_profile)
    if detected_industry and detected_industry in INDUSTRY_KEYWORDS:
        industry_keywords = set(INDUSTRY_KEYWORDS[detected_industry])
        matching_keywords = profile_keywords.intersection(industry_keywords)
        
        if len(matching_keywords) >= 10:
            keyword_score = 10
        elif len(matching_keywords) >= 5:
            keyword_score = 7
        elif len(matching_keywords) >= 3:
            keyword_score = 5
        else:
            keyword_score = 3
            issues.append(f"Adicione mais palavras-chave da área de {detected_industry}")
    else:
        keyword_score = 5  # Score neutro se não detectar indústria
    
    section_scores["keywords"] = keyword_score
    score += keyword_score
    
    # Calcula percentual final
    percentage = int((score / max_score) * 100)
    
    # Determina status
    if percentage >= 85:
        status = "Excelente"
    elif percentage >= 70:
        status = "Bom"
    elif percentage >= 50:
        status = "Regular"
    else:
        status = "Precisa melhorar"
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "status": status,
        "section_scores": section_scores,
        "issues": issues,
        "detected_industry": detected_industry
    }


def detect_user_industry(user_profile: Dict[str, Any]) -> str:
    """
    Detecta a indústria/área do usuário baseado no perfil.
    
    Args:
        user_profile: Perfil do usuário
        
    Returns:
        String com a indústria detectada ou None
    """
    # Coleta todo o texto relevante do perfil
    profile_text = ""
    
    # Adiciona texto dos campos relevantes
    for field in ["visao_atual", "visao_futuro", "wishPositions"]:
        if user_profile.get(field):
            if isinstance(user_profile[field], list):
                profile_text += " ".join(user_profile[field]) + " "
            else:
                profile_text += str(user_profile[field]) + " "
    
    # Adiciona experiências
    for exp in user_profile.get("experiences", []):
        profile_text += exp.get("position", "") + " "
        profile_text += exp.get("activity", "") + " "
    
    # Adiciona habilidades
    for skill in user_profile.get("hardSkills", []):
        profile_text += skill + " "
    
    profile_text = profile_text.lower()
    
    # Conta matches por indústria
    industry_matches = {}
    
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        matches = 0
        for keyword in keywords:
            if keyword.lower() in profile_text:
                matches += 1
        if matches > 0:
            industry_matches[industry] = matches
    
    # Retorna a indústria com mais matches
    if industry_matches:
        return max(industry_matches, key=industry_matches.get)
    
    return None


def generate_ats_report(user_profile: Dict[str, Any]) -> str:
    """
    Gera um relatório detalhado de compatibilidade ATS.
    
    Args:
        user_profile: Perfil do usuário
        
    Returns:
        String com relatório formatado
    """
    analysis = calculate_ats_score(user_profile)
    
    report = f"""## 📊 Análise de Compatibilidade ATS

**Score Geral: {analysis['percentage']}% - {analysis['status']}**

### Análise por Seção:
"""
    
    section_names = {
        "contact": "Informações de Contato",
        "summary": "Resumo Profissional",
        "experience": "Experiências",
        "education": "Formação",
        "skills": "Habilidades",
        "formatting": "Formatação",
        "keywords": "Palavras-chave"
    }
    
    for section, score in analysis['section_scores'].items():
        max_scores = {
            "contact": 10,
            "summary": 15,
            "experience": 25,
            "education": 10,
            "skills": 15,
            "formatting": 15,
            "keywords": 10
        }
        
        percentage = int((score / max_scores[section]) * 100)
        status_emoji = "✅" if percentage >= 80 else "⚠️" if percentage >= 60 else "❌"
        
        report += f"\n{status_emoji} **{section_names[section]}**: {score}/{max_scores[section]} ({percentage}%)"
    
    if analysis['issues']:
        report += "\n\n### 🔍 Problemas Encontrados:\n"
        for i, issue in enumerate(analysis['issues'], 1):
            report += f"{i}. {issue}\n"
    
    if analysis['detected_industry']:
        report += f"\n### 🏢 Área Detectada: {analysis['detected_industry'].title()}"
    
    return report


def optimize_profile_for_ats(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera sugestões de otimização para o perfil.
    
    Args:
        user_profile: Perfil do usuário
        
    Returns:
        Dicionário com sugestões de otimização
    """
    suggestions = {
        "immediate": [],  # Ações imediatas
        "improvements": [],  # Melhorias gerais
        "keywords_to_add": [],  # Palavras-chave sugeridas
        "formatting_fixes": []  # Correções de formatação
    }
    
    analysis = calculate_ats_score(user_profile)
    
    # Sugestões baseadas no score de cada seção
    scores = analysis['section_scores']
    
    # Contato
    if scores['contact'] < 10:
        if not user_profile.get("email"):
            suggestions["immediate"].append("Adicione seu email profissional")
        if not user_profile.get("phone"):
            suggestions["immediate"].append("Adicione seu telefone com DDD")
        if not user_profile.get("city") or not user_profile.get("state"):
            suggestions["immediate"].append("Complete sua localização (cidade e estado)")
    
    # Resumo profissional
    if scores['summary'] < 15:
        if not user_profile.get("visao_atual"):
            suggestions["immediate"].append(
                "Crie um resumo profissional de 3-4 linhas destacando sua experiência e objetivos"
            )
        else:
            suggestions["improvements"].append(
                "Expanda seu resumo profissional incluindo suas principais realizações"
            )
    
    # Experiências
    if scores['experience'] < 20:
        experiences = user_profile.get("experiences", [])
        if not experiences:
            suggestions["immediate"].append("Adicione suas experiências profissionais")
        else:
            suggestions["improvements"].append(
                "Comece cada descrição de experiência com um verbo de ação (Desenvolvi, Gerenciei, etc.)"
            )
            suggestions["improvements"].append(
                "Adicione conquistas quantificadas (ex: 'Aumentei vendas em 30%')"
            )
    
    # Habilidades
    if scores['skills'] < 12:
        if len(user_profile.get("hardSkills", [])) < 5:
            suggestions["immediate"].append("Adicione pelo menos 5 habilidades técnicas relevantes")
        if len(user_profile.get("softSkills", [])) < 3:
            suggestions["improvements"].append("Inclua 3-5 habilidades comportamentais")
    
    # Palavras-chave
    if analysis['detected_industry']:
        industry = analysis['detected_industry']
        industry_keywords = set(INDUSTRY_KEYWORDS.get(industry, []))
        
        # Extrai palavras atuais do perfil
        current_keywords = set()
        profile_text = ""
        
        for field in ["visao_atual", "visao_futuro"]:
            if user_profile.get(field):
                profile_text += str(user_profile[field]) + " "
        
        for exp in user_profile.get("experiences", []):
            profile_text += exp.get("activity", "") + " "
        
        current_keywords = set(extract_keywords_from_text(profile_text))
        
        # Sugere palavras que estão faltando
        missing_keywords = industry_keywords - current_keywords
        if missing_keywords:
            suggestions["keywords_to_add"] = list(missing_keywords)[:10]
            suggestions["improvements"].append(
                f"Inclua palavras-chave relevantes para {industry}: {', '.join(list(missing_keywords)[:5])}"
            )
    
    # Formatação
    profile_text = str(user_profile)
    for problematic, replacement in PROBLEMATIC_TERMS.items():
        if problematic in profile_text:
            suggestions["formatting_fixes"].append(f"Substitua '{problematic}' por '{replacement}'")
    
    return suggestions


def create_optimized_experience_description(
    position: str,
    activities: str,
    industry: str = None
) -> str:
    """
    Cria uma descrição otimizada de experiência profissional.
    
    Args:
        position: Cargo ocupado
        activities: Descrição das atividades
        industry: Indústria/área (opcional)
        
    Returns:
        String com descrição otimizada
    """
    optimized_lines = []
    
    # Extrai atividades individuais
    activity_list = activities.split(".")
    
    for activity in activity_list:
        activity = activity.strip()
        if not activity:
            continue
        
        # Verifica se já começa com verbo de ação
        starts_with_verb = False
        for verbs in ACTION_VERBS.values():
            for verb in verbs:
                if activity.lower().startswith(verb.lower()):
                    starts_with_verb = True
                    break
            if starts_with_verb:
                break
        
        # Se não começa com verbo, adiciona um apropriado
        if not starts_with_verb:
            # Escolhe categoria de verbo baseado no conteúdo
            if any(word in activity.lower() for word in ["equipe", "time", "pessoas"]):
                verb = "Gerenciei"
            elif any(word in activity.lower() for word in ["sistema", "software", "aplicação"]):
                verb = "Desenvolvi"
            elif any(word in activity.lower() for word in ["processo", "melhoria", "otimização"]):
                verb = "Otimizei"
            elif any(word in activity.lower() for word in ["análise", "relatório", "dados"]):
                verb = "Analisei"
            else:
                verb = "Executei"
            
            activity = f"{verb} {activity.lower()}"
        
        # Adiciona bullet point
        optimized_lines.append(f"• {activity}")
    
    return "\n".join(optimized_lines)


def analyze_profile_keywords(user_profile: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Analisa e extrai todas as palavras-chave relevantes do perfil.
    
    Args:
        user_profile: Perfil do usuário
        
    Returns:
        Dicionário com palavras-chave por categoria
    """
    keywords = {
        "technical": [],
        "soft_skills": [],
        "general": [],
        "industry_specific": []
    }
    
    # Habilidades técnicas
    keywords["technical"] = user_profile.get("hardSkills", [])
    
    # Habilidades comportamentais
    keywords["soft_skills"] = user_profile.get("softSkills", [])
    
    # Palavras gerais do perfil
    profile_text = ""
    for field in ["visao_atual", "visao_futuro"]:
        if user_profile.get(field):
            profile_text += str(user_profile[field]) + " "
    
    for exp in user_profile.get("experiences", []):
        profile_text += exp.get("activity", "") + " "
    
    keywords["general"] = extract_keywords_from_text(profile_text)
    
    # Palavras específicas da indústria
    detected_industry = detect_user_industry(user_profile)
    if detected_industry:
        industry_keywords = INDUSTRY_KEYWORDS.get(detected_industry, [])
        # Filtra apenas as que aparecem no perfil
        keywords["industry_specific"] = [
            kw for kw in industry_keywords 
            if kw.lower() in profile_text.lower()
        ]
    
    return keywords