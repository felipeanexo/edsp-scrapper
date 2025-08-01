# 📊 Dashboard EDSP - Escolas de São Paulo

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Playwright](https://img.shields.io/badge/Playwright-Automação%20Web-green.svg)
![Power BI](https://img.shields.io/badge/Power%20BI-Visualização-orange.svg)
![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Hospedagem-lightgrey.svg)

**Um dashboard interativo que apresenta dados completos das escolas do estado de São Paulo, desenvolvido com Power BI e hospedado no GitHub Pages.**

[🌐 Acessar Dashboard](https://felipeanexo.github.io/edsp-scrapper) | [📊 Ver Dados](https://github.com/felipeanexo/edsp-scrapper/tree/main/results)

</div>

---

## 🎯 Sobre o Projeto

Este projeto coleta e analisa dados de **5.575+ escolas** do estado de São Paulo, processando **558 páginas** de dados com **100% de taxa de sucesso**. O dashboard apresenta informações detalhadas sobre cada instituição educacional, fornecendo insights valiosos para pesquisadores, educadores e gestores públicos.

### 📈 Estatísticas Impressionantes

| Métrica | Valor |
|---------|-------|
| 🏫 Escolas Processadas | **5.575+** |
| 📄 Páginas de Dados | **558** |
| ✅ Taxa de Sucesso | **100%** |
| 📊 Campos por Escola | **25+** |
| ⏱️ Tempo de Processamento | **~2 horas** |

---

## 📊 Dados Coletados

### 🏫 Informações Básicas
- **Nome da escola** e classificação (PEI/EE)
- **Diretoria de ensino** e região administrativa
- **Endereço completo** (município, bairro, logradouro)

### 📞 Contato e Localização
- **Telefone** institucional
- **Email** oficial da escola
- **Município** e bairro detalhados

### 📈 Indicadores Educacionais
- **Notas IDEB** (Anos Finais e Ensino Médio)
- **Notas IDESP** (Anos Finais e Ensino Médio)
- **Comparação** com médias estaduais

### 👥 Dados dos Alunos
- **Total de estudantes** matriculados
- **Distribuição por faixa etária**:
  - 🧒 06 a 10 anos
  - 👦 11 a 14 anos  
  - 👨‍🎓 15 a 17 anos
  - 👨‍💼 Acima de 18 anos

### 🏢 Estrutura Escolar
- **Total de turmas** por nível
- **Turmas por segmento** (Anos Finais/Ensino Médio)
- **Total de salas de aula**

### 🏗️ Infraestrutura
- **Laboratórios** de ciências e informática
- **Quadras esportivas** e ginásios
- **Bibliotecas** e salas de leitura
- **Sala de informática** e recursos digitais
- **Outros ambientes** especializados

---

## 🚀 Tecnologias Utilizadas

### 🔧 Backend (Scraping)
- **Python 3.12+** - Linguagem principal
- **Playwright** - Automação avançada de navegação web
- **BeautifulSoup** - Parsing eficiente de HTML
- **Poetry** - Gerenciamento moderno de dependências
- **Asyncio** - Processamento assíncrono de alta performance

### 🎨 Frontend (Dashboard)
- **Power BI** - Visualização profissional e análise de dados
- **HTML5/CSS3** - Interface responsiva e moderna
- **GitHub Pages** - Hospedagem gratuita e confiável

### 🏗️ Arquitetura
- **Clean Architecture** - Separação clara de responsabilidades
- **Structured Logging** - Logs estruturados para monitoramento
- **Error Handling** - Tratamento robusto de erros
- **Batch Processing** - Processamento eficiente em lotes

---

## 🛠️ Como Executar

### 📋 Pré-requisitos
- Python 3.12+
- Poetry (gerenciador de dependências)
- Git

### ⚡ Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/felipeanexo/edsp-scrapper.git
cd edsp-scrapper

# 2. Instale as dependências
poetry install

# 3. Instale os navegadores do Playwright
poetry run playwright install

# 4. Execute o scraper
poetry run python main.py sample  # 🧪 Para testar (5 páginas)
poetry run python main.py         # 🚀 Para processar tudo (558 páginas)
```

### 📁 Estrutura do Projeto

```
edsp-scrapper/
├── 📊 index.html              # Dashboard principal
├── 📖 README.md               # Documentação
├── 🔧 src/                    # Código do scraper
│   ├── domain/               # Entidades de domínio
│   ├── application/          # Lógica de aplicação
│   └── infrastructure/       # Infraestrutura
├── 📈 results/               # Dados coletados (CSV)
├── 📝 logs/                  # Logs de execução
└── ⚙️ pyproject.toml         # Configuração Poetry
```

---

## 📱 Acesso ao Dashboard

### 🌐 URL Principal
**https://felipeanexo.github.io/edsp-scrapper**

### 📊 Funcionalidades do Dashboard
- **📈 Visualização Interativa** - Gráficos e tabelas dinâmicas
- **🔍 Filtros Avançados** - Por região, classificação, indicadores
- **📊 Análise Comparativa** - Comparação entre escolas
- **📥 Exportação de Dados** - Dados em formato CSV
- **📱 Design Responsivo** - Funciona perfeitamente em desktop e mobile

---

## 🔧 Configuração do GitHub Pages

### 1. **Ativar GitHub Pages**
1. Vá para **Settings** > **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: main
4. **Folder**: / (root)
5. Clique em **Save**

### 2. **Deploy Automático**
O projeto já inclui workflows do GitHub Actions para deploy automático:
- `.github/workflows/deploy.yml` - Deploy tradicional
- `.github/workflows/static.yml` - Deploy estático (recomendado)

### 3. **SEO Otimizado**
- `robots.txt` - Configuração para crawlers
- `sitemap.xml` - Mapa do site para SEO
- Meta tags otimizadas no HTML

---

## 📈 Exemplo de Dados Coletados

```csv
school_name,classification,detail_url,extraction_timestamp,status,teaching_directorate,neighborhood,municipality,phone,email,ideb_score_final_years,idesp_score_final_years,ideb_score_high_school,idesp_score_high_school,total_students,age_06_10_final_years,age_11_14_final_years,age_15_17_final_years,age_18_plus_final_years,age_06_10_high_school,age_11_14_high_school,age_15_17_high_school,age_18_plus_high_school,total_classes,classes_final_years,classes_high_school,total_classrooms,error_message
16 DE JULHO,PEI,https://transparencia.educacao.sp.gov.br/Home/DetalhesEscola?codesc=923370,2025-07-29T15:01:10.237596,SUCCESS,SUL 1,São Paulo,São Paulo,(11) 1234-5678,escola@example.com,4.60,3.65,5.10,2.90,361,1,267,17,,,73,3,12,9,3,15,
```

---

## 🎨 Características Técnicas

### 🏗️ Clean Architecture
- **Domain Layer** - Lógica de negócio pura
- **Application Layer** - Casos de uso e serviços
- **Infrastructure Layer** - Preocupações externas

### 📊 Structured Logging
- **Context Binding** - Logs com contexto relevante
- **Performance Metrics** - Métricas de tempo e estatísticas
- **Error Tracking** - Rastreamento detalhado de erros

### ⚡ Performance
- **Parallel Processing** - Processamento paralelo real
- **Memory Efficient** - Uso otimizado de memória
- **Rate Limiting** - Delays inteligentes
- **Retry Logic** - Lógica de retry robusta

---

## 🤝 Contribuição

Contribuições são muito bem-vindas! Para contribuir:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

### 📋 Diretrizes de Contribuição
- Siga os princípios da **Clean Architecture**
- Adicione **logs estruturados** para novas funcionalidades
- Inclua **tratamento de erros** robusto
- Mantenha a **documentação** atualizada

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo `LICENSE` para mais detalhes.

---

## 📞 Contato

- **👨‍💻 Desenvolvedor**: Felipe Anexo
- **📧 Email**: felipe.versiane@institutoanexo.com.br
- **💼 LinkedIn**: [@felipeversiane](https://linkedin.com/in/felipeversiane)
- **🐙 GitHub**: [@felipeanexo](https://github.com/felipeanexo)

---

## 🙏 Agradecimentos

- **🏛️ SEDUC-SP** - Pela disponibilização dos dados educacionais
- **📊 Power BI** - Pela plataforma de visualização profissional
- **🚀 GitHub** - Pela hospedagem gratuita e ferramentas
- **🐍 Python Community** - Pela linguagem e ecossistema
- **🌐 Playwright Team** - Pela ferramenta de automação web

---

<div align="center">

⭐ **Se este projeto foi útil para você, considere dar uma estrela no repositório!**

[![GitHub stars](https://img.shields.io/github/stars/felipeanexo/edsp-scrapper?style=social)](https://github.com/felipeanexo/edsp-scrapper)

**Desenvolvido com ❤️ para a educação de São Paulo**

</div>
