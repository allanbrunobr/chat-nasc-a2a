/**
 * Cloud Function para análise de gaps entre candidato e vaga
 * 
 * @param {Object} req - Request object
 * @param {Object} res - Response object
 */

const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

// Pesos para cálculo de compatibilidade
const WEIGHTS = {
  hardSkills: 0.35,
  experience: 0.25,
  education: 0.15,
  languages: 0.10,
  certifications: 0.10,
  location: 0.05
};

// Mapeamento de níveis de educação (ordem de importância)
const EDUCATION_LEVELS = {
  'ELEMENTARY_EDUCATION': 1,
  'HIGH_SCHOOL': 2,
  'TECHNICIAN': 3,
  'TECHNOLOGIST': 4,
  'UNDERGRADUATE': 5,
  'BACHELORS': 5,
  'TEACHING': 5,
  'POSTGRADUATE': 6,
  'MASTER': 7,
  'DOCTORATE': 8
};

// Mapeamento de níveis de idioma
const LANGUAGE_LEVELS = {
  'BEGINNER': 1,
  'INTERMEDIATE': 2,
  'ADVANCED': 3,
  'PROFICIENT': 4,
  'FLUENT': 5,
  'BILINGUAL': 6,
  'NATIVE': 7
};

exports.analyzeCandidateGaps = async (req, res) => {
  // Configurar CORS
  res.set('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') {
    res.set('Access-Control-Allow-Methods', 'POST');
    res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.status(204).send('');
    return;
  }

  try {
    const { userId, vacancyId } = req.body;

    if (!userId || !vacancyId) {
      return res.status(400).json({
        error: 'userId e vacancyId são obrigatórios'
      });
    }

    // Buscar dados do candidato
    const userProfile = await getUserCompleteProfile(userId);
    if (!userProfile) {
      return res.status(404).json({
        error: 'Perfil do usuário não encontrado'
      });
    }

    // Buscar dados da vaga
    const vacancy = await getVacancyDetails(vacancyId);
    if (!vacancy) {
      return res.status(404).json({
        error: 'Vaga não encontrada'
      });
    }

    // Analisar gaps
    const gapAnalysis = await analyzeGaps(userProfile, vacancy);

    // Buscar sugestões de melhoria
    const suggestions = await getSuggestions(gapAnalysis.gaps);

    // Calcular score de compatibilidade
    const compatibilityScore = calculateCompatibilityScore(gapAnalysis);

    // Montar resposta
    const response = {
      vacancy: {
        id: vacancy.id,
        title: vacancy.title,
        company: vacancy.company.companyName,
        location: vacancy.location
      },
      currentCompatibility: compatibilityScore,
      gaps: gapAnalysis.gaps,
      matches: gapAnalysis.matches,
      suggestions: suggestions,
      improvementPotential: calculateImprovementPotential(gapAnalysis.gaps),
      actionPlan: generateActionPlan(gapAnalysis.gaps, suggestions)
    };

    res.status(200).json(response);

  } catch (error) {
    console.error('Erro na análise de gaps:', error);
    res.status(500).json({
      error: 'Erro ao processar análise de gaps',
      details: error.message
    });
  } finally {
    await prisma.$disconnect();
  }
};

/**
 * Busca perfil completo do usuário
 */
async function getUserCompleteProfile(userId) {
  return await prisma.user.findUnique({
    where: { id: userId },
    include: {
      cv: {
        include: {
          hardSkills: true,
          softSkills: true,
          languages: true,
          professionalExperiences: true,
          CvEducation: true,
          CvCertification: true,
          CvAditionalCourse: true
        }
      },
      complement: true,
      userEmbeddings: true
    }
  });
}

/**
 * Busca detalhes da vaga
 */
async function getVacancyDetails(vacancyId) {
  return await prisma.jobVacancy.findUnique({
    where: { id: parseInt(vacancyId) },
    include: {
      company: true,
      address: true,
      VacancyEmbeddings: true
    }
  });
}

/**
 * Analisa gaps entre candidato e vaga
 */
async function analyzeGaps(userProfile, vacancy) {
  const gaps = [];
  const matches = [];

  // 1. Análise de Hard Skills
  const skillsAnalysis = analyzeSkillGaps(userProfile, vacancy);
  gaps.push(...skillsAnalysis.gaps);
  matches.push(...skillsAnalysis.matches);

  // 2. Análise de Experiência
  const experienceAnalysis = analyzeExperienceGaps(userProfile, vacancy);
  if (experienceAnalysis.gap) gaps.push(experienceAnalysis.gap);
  if (experienceAnalysis.match) matches.push(experienceAnalysis.match);

  // 3. Análise de Educação
  const educationAnalysis = analyzeEducationGaps(userProfile, vacancy);
  if (educationAnalysis.gap) gaps.push(educationAnalysis.gap);
  if (educationAnalysis.match) matches.push(educationAnalysis.match);

  // 4. Análise de Idiomas
  const languageAnalysis = analyzeLanguageGaps(userProfile, vacancy);
  gaps.push(...languageAnalysis.gaps);
  matches.push(...languageAnalysis.matches);

  // 5. Análise de Certificações
  const certificationAnalysis = analyzeCertificationGaps(userProfile, vacancy);
  gaps.push(...certificationAnalysis.gaps);
  matches.push(...certificationAnalysis.matches);

  // 6. Análise de Localização
  const locationAnalysis = analyzeLocationGaps(userProfile, vacancy);
  if (locationAnalysis.gap) gaps.push(locationAnalysis.gap);
  if (locationAnalysis.match) matches.push(locationAnalysis.match);

  return { gaps, matches };
}

/**
 * Analisa gaps de habilidades
 */
function analyzeSkillGaps(userProfile, vacancy) {
  const gaps = [];
  const matches = [];
  
  // Extrair skills requeridas da descrição da vaga
  const requiredSkills = extractRequiredSkills(vacancy);
  const userSkills = userProfile.cv?.hardSkills || [];
  const userSkillNames = userSkills.map(s => s.skill.toLowerCase());

  requiredSkills.forEach(skill => {
    const hasSkill = userSkillNames.includes(skill.name.toLowerCase());
    
    if (!hasSkill) {
      gaps.push({
        type: 'hardSkill',
        name: skill.name,
        severity: skill.mandatory ? 'high' : 'medium',
        description: `Habilidade "${skill.name}" é ${skill.mandatory ? 'obrigatória' : 'desejável'} mas não consta no seu perfil`,
        category: 'skills'
      });
    } else {
      matches.push({
        type: 'hardSkill',
        name: skill.name,
        description: `Você possui a habilidade "${skill.name}"`
      });
    }
  });

  return { gaps, matches };
}

/**
 * Extrai skills requeridas da descrição da vaga
 */
function extractRequiredSkills(vacancy) {
  // Lista de tecnologias comuns para buscar na descrição
  const commonSkills = [
    'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue', 'Node.js',
    'Python', 'Django', 'Flask', 'Java', 'Spring', 'C#', '.NET',
    'PHP', 'Laravel', 'Ruby', 'Rails', 'Go', 'Rust', 'Swift',
    'Kotlin', 'Flutter', 'React Native', 'Docker', 'Kubernetes',
    'AWS', 'Azure', 'GCP', 'MongoDB', 'PostgreSQL', 'MySQL',
    'Redis', 'ElasticSearch', 'GraphQL', 'REST', 'Git', 'CI/CD',
    'Scrum', 'Agile', 'DevOps', 'Machine Learning', 'Data Science'
  ];

  const description = (vacancy.description || '').toLowerCase();
  const qualification = (vacancy.requiredQualification || '').toLowerCase();
  const fullText = `${description} ${qualification}`;

  const foundSkills = [];

  commonSkills.forEach(skill => {
    if (fullText.includes(skill.toLowerCase())) {
      // Determinar se é obrigatório baseado em palavras-chave
      const mandatory = fullText.includes(`${skill.toLowerCase()} obrigatório`) ||
                       fullText.includes(`experiência em ${skill.toLowerCase()}`) ||
                       fullText.includes(`domínio de ${skill.toLowerCase()}`);
      
      foundSkills.push({
        name: skill,
        mandatory: mandatory
      });
    }
  });

  return foundSkills;
}

/**
 * Analisa gaps de experiência
 */
function analyzeExperienceGaps(userProfile, vacancy) {
  const experiences = userProfile.cv?.professionalExperiences || [];
  const totalYears = calculateTotalExperience(experiences);
  
  // Extrair anos de experiência requeridos
  const requiredYears = extractRequiredExperience(vacancy);
  
  if (requiredYears > 0) {
    if (totalYears < requiredYears) {
      return {
        gap: {
          type: 'experience',
          name: 'Tempo de experiência',
          required: requiredYears,
          current: totalYears,
          severity: 'high',
          description: `Vaga requer ${requiredYears} anos de experiência, você tem ${totalYears.toFixed(1)} anos`,
          category: 'experience'
        }
      };
    } else {
      return {
        match: {
          type: 'experience',
          name: 'Tempo de experiência',
          description: `Você possui ${totalYears.toFixed(1)} anos de experiência (requerido: ${requiredYears})`
        }
      };
    }
  }

  return {};
}

/**
 * Calcula total de anos de experiência
 */
function calculateTotalExperience(experiences) {
  let totalMonths = 0;
  
  experiences.forEach(exp => {
    const start = new Date(exp.startDate);
    const end = exp.endDate ? new Date(exp.endDate) : new Date();
    const months = (end - start) / (1000 * 60 * 60 * 24 * 30);
    totalMonths += months;
  });

  return totalMonths / 12;
}

/**
 * Extrai anos de experiência requeridos
 */
function extractRequiredExperience(vacancy) {
  const text = `${vacancy.description} ${vacancy.requiredQualification}`.toLowerCase();
  
  // Padrões para buscar anos de experiência
  const patterns = [
    /(\d+)\s*anos?\s*de\s*experiência/i,
    /experiência\s*de\s*(\d+)\s*anos?/i,
    /mínimo\s*de\s*(\d+)\s*anos?/i,
    /pelo\s*menos\s*(\d+)\s*anos?/i
  ];

  for (let pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return parseInt(match[1]);
    }
  }

  // Se requiresExperience é true mas não especifica anos, assumir 2 anos
  if (vacancy.requiresExperience) {
    return 2;
  }

  return 0;
}

/**
 * Analisa gaps de educação
 */
function analyzeEducationGaps(userProfile, vacancy) {
  const userEducation = userProfile.cv?.CvEducation || [];
  const highestUserEducation = getHighestEducation(userEducation);
  const requiredEducation = vacancy.educationLevel;

  if (requiredEducation && EDUCATION_LEVELS[requiredEducation]) {
    const requiredLevel = EDUCATION_LEVELS[requiredEducation];
    const userLevel = EDUCATION_LEVELS[highestUserEducation] || 0;

    if (userLevel < requiredLevel) {
      return {
        gap: {
          type: 'education',
          name: 'Formação acadêmica',
          required: requiredEducation,
          current: highestUserEducation || 'Não informado',
          severity: 'medium',
          description: `Vaga requer ${formatEducationLevel(requiredEducation)}, você possui ${formatEducationLevel(highestUserEducation)}`,
          category: 'education'
        }
      };
    } else {
      return {
        match: {
          type: 'education',
          name: 'Formação acadêmica',
          description: `Você atende o requisito de formação (${formatEducationLevel(highestUserEducation)})`
        }
      };
    }
  }

  return {};
}

/**
 * Obtém maior nível de educação
 */
function getHighestEducation(educationList) {
  let highestLevel = null;
  let highestValue = 0;

  educationList.forEach(edu => {
    const level = EDUCATION_LEVELS[edu.courseType];
    if (level && level > highestValue) {
      highestValue = level;
      highestLevel = edu.courseType;
    }
  });

  return highestLevel;
}

/**
 * Formata nível de educação para exibição
 */
function formatEducationLevel(level) {
  const labels = {
    'ELEMENTARY_EDUCATION': 'Ensino Fundamental',
    'HIGH_SCHOOL': 'Ensino Médio',
    'TECHNICIAN': 'Técnico',
    'TECHNOLOGIST': 'Tecnólogo',
    'UNDERGRADUATE': 'Graduação',
    'BACHELORS': 'Bacharelado',
    'TEACHING': 'Licenciatura',
    'POSTGRADUATE': 'Pós-graduação',
    'MASTER': 'Mestrado',
    'DOCTORATE': 'Doutorado'
  };

  return labels[level] || level || 'Não informado';
}

/**
 * Analisa gaps de idiomas
 */
function analyzeLanguageGaps(userProfile, vacancy) {
  const gaps = [];
  const matches = [];
  
  // Extrair idiomas requeridos
  const requiredLanguages = extractRequiredLanguages(vacancy);
  const userLanguages = userProfile.cv?.languages || [];

  requiredLanguages.forEach(reqLang => {
    const userLang = userLanguages.find(l => 
      l.language.toLowerCase() === reqLang.name.toLowerCase()
    );

    if (!userLang) {
      gaps.push({
        type: 'language',
        name: reqLang.name,
        required: reqLang.level,
        severity: reqLang.mandatory ? 'high' : 'low',
        description: `Idioma ${reqLang.name} (${reqLang.level}) é ${reqLang.mandatory ? 'obrigatório' : 'desejável'}`,
        category: 'languages'
      });
    } else {
      const userLevel = LANGUAGE_LEVELS[userLang.level] || 0;
      const reqLevel = LANGUAGE_LEVELS[reqLang.level] || 0;

      if (userLevel < reqLevel) {
        gaps.push({
          type: 'language',
          name: reqLang.name,
          required: reqLang.level,
          current: userLang.level,
          severity: 'medium',
          description: `${reqLang.name}: você possui ${userLang.level}, vaga requer ${reqLang.level}`,
          category: 'languages'
        });
      } else {
        matches.push({
          type: 'language',
          name: reqLang.name,
          description: `Você atende o requisito de ${reqLang.name} (${userLang.level})`
        });
      }
    }
  });

  return { gaps, matches };
}

/**
 * Extrai idiomas requeridos
 */
function extractRequiredLanguages(vacancy) {
  const text = `${vacancy.description} ${vacancy.requiredQualification}`.toLowerCase();
  const languages = [];

  // Padrões de idiomas
  const langPatterns = {
    'Inglês': ['inglês', 'english'],
    'Espanhol': ['espanhol', 'spanish', 'español'],
    'Francês': ['francês', 'french', 'français'],
    'Alemão': ['alemão', 'german', 'deutsch'],
    'Italiano': ['italiano', 'italian'],
    'Mandarim': ['mandarim', 'chinês', 'chinese', 'mandarin']
  };

  Object.entries(langPatterns).forEach(([lang, patterns]) => {
    patterns.forEach(pattern => {
      if (text.includes(pattern)) {
        // Determinar nível
        let level = 'INTERMEDIATE'; // padrão
        if (text.includes(`${pattern} fluente`) || text.includes(`${pattern} avançado`)) {
          level = 'FLUENT';
        } else if (text.includes(`${pattern} intermediário`)) {
          level = 'INTERMEDIATE';
        } else if (text.includes(`${pattern} básico`)) {
          level = 'BEGINNER';
        }

        // Determinar se é obrigatório
        const mandatory = text.includes(`${pattern} obrigatório`) || 
                         text.includes(`${pattern} essencial`) ||
                         text.includes(`${pattern} imprescindível`);

        languages.push({
          name: lang,
          level: level,
          mandatory: mandatory
        });
      }
    });
  });

  return languages;
}

/**
 * Analisa gaps de certificações
 */
function analyzeCertificationGaps(userProfile, vacancy) {
  const gaps = [];
  const matches = [];
  
  // Extrair certificações requeridas
  const requiredCerts = extractRequiredCertifications(vacancy);
  const userCerts = userProfile.cv?.CvCertification || [];
  const userCertNames = userCerts.map(c => c.name.toLowerCase());

  requiredCerts.forEach(cert => {
    const hasCert = userCertNames.some(name => 
      name.includes(cert.name.toLowerCase()) || 
      cert.keywords.some(keyword => name.includes(keyword.toLowerCase()))
    );

    if (!hasCert) {
      gaps.push({
        type: 'certification',
        name: cert.name,
        severity: cert.mandatory ? 'high' : 'low',
        description: `Certificação ${cert.name} ${cert.mandatory ? 'é obrigatória' : 'é um diferencial'}`,
        category: 'certifications'
      });
    } else {
      matches.push({
        type: 'certification',
        name: cert.name,
        description: `Você possui certificação em ${cert.name}`
      });
    }
  });

  return { gaps, matches };
}

/**
 * Extrai certificações requeridas
 */
function extractRequiredCertifications(vacancy) {
  const text = `${vacancy.description} ${vacancy.requiredQualification}`.toLowerCase();
  const certifications = [];

  // Certificações comuns
  const certPatterns = [
    {
      name: 'AWS Certified',
      keywords: ['aws certified', 'aws certification', 'amazon web services']
    },
    {
      name: 'Azure',
      keywords: ['azure certified', 'microsoft azure', 'az-']
    },
    {
      name: 'Google Cloud',
      keywords: ['gcp certified', 'google cloud', 'google cloud platform']
    },
    {
      name: 'Scrum',
      keywords: ['scrum master', 'scrum certified', 'csm', 'psm']
    },
    {
      name: 'PMP',
      keywords: ['pmp', 'project management professional']
    },
    {
      name: 'ITIL',
      keywords: ['itil', 'it service management']
    },
    {
      name: 'Java Certified',
      keywords: ['java certified', 'ocp java', 'oracle certified']
    },
    {
      name: 'Microsoft Certified',
      keywords: ['microsoft certified', 'mcsa', 'mcse', 'mcp']
    }
  ];

  certPatterns.forEach(cert => {
    const found = cert.keywords.some(keyword => text.includes(keyword));
    if (found) {
      const mandatory = cert.keywords.some(keyword => 
        text.includes(`${keyword} obrigatório`) ||
        text.includes(`${keyword} essencial`) ||
        text.includes(`certificação ${keyword}`)
      );

      certifications.push({
        name: cert.name,
        keywords: cert.keywords,
        mandatory: mandatory
      });
    }
  });

  return certifications;
}

/**
 * Analisa gaps de localização
 */
function analyzeLocationGaps(userProfile, vacancy) {
  // Se a vaga é remota, não há gap de localização
  if (vacancy.workFormat === 'REMOTE') {
    return {
      match: {
        type: 'location',
        name: 'Localização',
        description: 'Vaga remota - localização não é um impedimento'
      }
    };
  }

  const userCity = userProfile.complement?.city;
  const userState = userProfile.complement?.state;
  const vacancyLocation = vacancy.location || vacancy.address?.city;

  if (!userCity || !vacancyLocation) {
    return {};
  }

  // Verificar se é a mesma cidade ou região metropolitana
  const isSameLocation = userCity.toLowerCase() === vacancyLocation.toLowerCase() ||
                        isMetropolitanArea(userCity, vacancyLocation);

  if (!isSameLocation && vacancy.workFormat === 'PRESENTIAL') {
    return {
      gap: {
        type: 'location',
        name: 'Localização',
        required: vacancyLocation,
        current: userCity,
        severity: 'high',
        description: `Vaga presencial em ${vacancyLocation}, você está em ${userCity}`,
        category: 'location'
      }
    };
  }

  return {
    match: {
      type: 'location',
      name: 'Localização',
      description: 'Localização compatível com a vaga'
    }
  };
}

/**
 * Verifica se duas cidades fazem parte da mesma região metropolitana
 */
function isMetropolitanArea(city1, city2) {
  // Regiões metropolitanas principais
  const metropolitanAreas = {
    'São Paulo': ['São Paulo', 'Guarulhos', 'São Bernardo do Campo', 'Santo André', 'Osasco', 'Diadema'],
    'Rio de Janeiro': ['Rio de Janeiro', 'Niterói', 'São Gonçalo', 'Duque de Caxias', 'Nova Iguaçu'],
    'Belo Horizonte': ['Belo Horizonte', 'Contagem', 'Betim', 'Ribeirão das Neves'],
    'Porto Alegre': ['Porto Alegre', 'Canoas', 'Gravataí', 'Viamão', 'Novo Hamburgo'],
    'Recife': ['Recife', 'Olinda', 'Jaboatão dos Guararapes', 'Paulista'],
    'Salvador': ['Salvador', 'Lauro de Freitas', 'Camaçari', 'Simões Filho'],
    'Curitiba': ['Curitiba', 'São José dos Pinhais', 'Colombo', 'Araucária']
  };

  for (let area of Object.values(metropolitanAreas)) {
    if (area.includes(city1) && area.includes(city2)) {
      return true;
    }
  }

  return false;
}

/**
 * Calcula score de compatibilidade
 */
function calculateCompatibilityScore(gapAnalysis) {
  let score = 100;
  
  // Penalizar por gaps
  gapAnalysis.gaps.forEach(gap => {
    const penalty = gap.severity === 'high' ? 15 : 
                   gap.severity === 'medium' ? 10 : 5;
    
    // Aplicar peso da categoria
    const categoryWeight = WEIGHTS[gap.category] || 0.1;
    score -= penalty * categoryWeight;
  });

  // Garantir que o score não seja negativo
  return Math.max(0, Math.round(score));
}

/**
 * Calcula potencial de melhoria
 */
function calculateImprovementPotential(gaps) {
  let potential = 0;
  
  gaps.forEach(gap => {
    // Gaps de skills e certificações podem ser resolvidos mais facilmente
    if (gap.type === 'hardSkill' || gap.type === 'certification') {
      potential += gap.severity === 'high' ? 15 : 10;
    }
    // Idiomas podem ser melhorados com tempo
    else if (gap.type === 'language') {
      potential += gap.severity === 'high' ? 10 : 5;
    }
    // Experiência e educação são mais difíceis de resolver rapidamente
    else if (gap.type === 'experience' || gap.type === 'education') {
      potential += gap.severity === 'high' ? 5 : 3;
    }
  });

  return Math.min(100, potential);
}

/**
 * Busca sugestões para cada gap
 */
async function getSuggestions(gaps) {
  const suggestions = [];

  for (let gap of gaps) {
    const suggestion = await generateSuggestion(gap);
    if (suggestion) {
      suggestions.push(suggestion);
    }
  }

  return suggestions;
}

/**
 * Gera sugestão para um gap específico
 */
async function generateSuggestion(gap) {
  const suggestion = {
    gapId: `${gap.type}_${gap.name}`,
    type: gap.type,
    priority: gap.severity,
    actions: []
  };

  switch (gap.type) {
    case 'hardSkill':
      suggestion.actions = [
        {
          type: 'course',
          title: `Curso de ${gap.name}`,
          provider: 'SENAI/SETASC',
          duration: '40-80 horas',
          cost: 'Gratuito'
        },
        {
          type: 'practice',
          title: `Projeto prático com ${gap.name}`,
          description: 'Desenvolva um projeto pessoal para portfolio',
          duration: '2-4 semanas'
        }
      ];
      suggestion.estimatedTime = '30-60 dias';
      break;

    case 'language':
      suggestion.actions = [
        {
          type: 'course',
          title: `Curso de ${gap.name} - ${gap.required}`,
          provider: 'Plataforma online',
          duration: '3-6 meses'
        },
        {
          type: 'practice',
          title: 'Prática diária',
          description: 'Conversação e leitura técnica',
          duration: '30 min/dia'
        }
      ];
      suggestion.estimatedTime = '3-6 meses';
      break;

    case 'certification':
      suggestion.actions = [
        {
          type: 'preparation',
          title: `Preparatório para ${gap.name}`,
          provider: 'Online',
          duration: '2-3 meses'
        },
        {
          type: 'exam',
          title: 'Exame de certificação',
          cost: 'Consultar valor'
        }
      ];
      suggestion.estimatedTime = '60-90 dias';
      break;

    case 'experience':
      suggestion.actions = [
        {
          type: 'project',
          title: 'Projetos freelance ou voluntários',
          description: 'Ganhe experiência prática na área',
          duration: 'Contínuo'
        },
        {
          type: 'portfolio',
          title: 'Construa um portfolio sólido',
          description: 'Demonstre suas habilidades através de projetos'
        }
      ];
      suggestion.estimatedTime = '6-12 meses';
      break;

    case 'education':
      suggestion.actions = [
        {
          type: 'education',
          title: `Buscar formação em ${gap.required}`,
          provider: 'Instituição de ensino',
          duration: 'Variável'
        },
        {
          type: 'alternative',
          title: 'Cursos técnicos ou especializações',
          description: 'Alternativas mais rápidas à graduação tradicional'
        }
      ];
      suggestion.estimatedTime = '1-4 anos';
      break;
  }

  return suggestion;
}

/**
 * Gera plano de ação ordenado por prioridade
 */
function generateActionPlan(gaps, suggestions) {
  const plan = {
    immediate: [],  // 0-30 dias
    shortTerm: [],  // 30-90 dias
    mediumTerm: [], // 3-6 meses
    longTerm: []    // 6+ meses
  };

  // Ordenar gaps por prioridade e facilidade de resolução
  const prioritizedGaps = gaps.sort((a, b) => {
    const priorityScore = {
      'high': 3,
      'medium': 2,
      'low': 1
    };
    
    const easinessScore = {
      'hardSkill': 3,
      'certification': 3,
      'language': 2,
      'experience': 1,
      'education': 1,
      'location': 0
    };

    const scoreA = priorityScore[a.severity] * easinessScore[a.type];
    const scoreB = priorityScore[b.severity] * easinessScore[b.type];
    
    return scoreB - scoreA;
  });

  // Distribuir ações no plano
  prioritizedGaps.forEach((gap, index) => {
    const suggestion = suggestions.find(s => s.gapId === `${gap.type}_${gap.name}`);
    
    if (suggestion) {
      const action = {
        gap: gap.name,
        type: gap.type,
        priority: gap.severity,
        actions: suggestion.actions,
        estimatedTime: suggestion.estimatedTime
      };

      // Distribuir baseado no tipo e prioridade
      if (gap.type === 'hardSkill' && gap.severity === 'high' && index < 2) {
        plan.immediate.push(action);
      } else if (gap.type === 'certification' || (gap.type === 'hardSkill' && index < 4)) {
        plan.shortTerm.push(action);
      } else if (gap.type === 'language' || gap.type === 'experience') {
        plan.mediumTerm.push(action);
      } else {
        plan.longTerm.push(action);
      }
    }
  });

  return plan;
}