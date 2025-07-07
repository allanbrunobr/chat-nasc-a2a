# Esclarecimento: Skills do Candidato vs Skills do Sistema

## 1. Skills do CANDIDATO (Habilidades Profissionais)
São as competências da PESSOA no currículo:

### Hard Skills (Habilidades Técnicas)
- Python
- Java  
- Machine Learning
- Excel
- Inglês

### Soft Skills (Habilidades Comportamentais)
- Liderança
- Trabalho em equipe
- Comunicação
- Resolução de problemas

**Onde aparecem**: No perfil/currículo do usuário
```python
profile_data = {
    "hardSkills": ["Python", "Java"],
    "softSkills": ["Liderança"]
}
```

## 2. Skills do SISTEMA A2A (Comandos/Funções)
São as AÇÕES que o sistema pode executar:

### Skills/Comandos disponíveis:
- `retrieve_user_profile` → Buscar perfil do usuário
- `save_user_profile` → Salvar perfil do usuário  
- `find_job_matches` → Buscar vagas de emprego
- `retrieve_gap` → Analisar lacunas de competências
- `retrieve_courses` → Buscar cursos

**Onde aparecem**: No metadata da mensagem A2A
```python
message = {
    "metadata": {
        "skill": "find_job_matches",  # ← Comando para o sistema executar
        "user_id": "123"
    }
}
```

## Analogia Simples:

### Skills do Candidato = Habilidades no CV
- "Eu sei Python"
- "Eu sei liderar equipes"
- "Eu falo inglês"

### Skills do Sistema = Botões/Comandos
- "Mostrar perfil"
- "Salvar dados"
- "Buscar vagas"
- "Encontrar cursos"

## No contexto do NAI:

1. O **candidato** tem suas skills (habilidades) no perfil
2. O **sistema** tem suas skills (comandos) que pode executar
3. Uma skill do sistema pode ser "buscar candidatos por suas skills profissionais"

## Exemplo prático:

```python
# Skill do SISTEMA sendo chamada
request = {
    "metadata": {
        "skill": "find_job_matches",  # ← Comando: "encontre vagas"
        "user_id": "joao123"
    }
}

# O sistema vai buscar vagas baseado nas skills do CANDIDATO
# que estão no perfil dele:
joao_profile = {
    "hardSkills": ["Python", "Java"],  # ← Habilidades do João
    "softSkills": ["Liderança"]
}
```

É como a diferença entre:
- **Habilidades do mecânico**: trocar óleo, consertar motor
- **Funções da oficina**: agendar serviço, emitir nota fiscal