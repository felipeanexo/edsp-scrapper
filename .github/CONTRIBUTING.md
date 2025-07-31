# Guia de Contribuição

Obrigado por considerar contribuir para o **Dashboard EDSP - Escolas de São Paulo**! 🎉

## Como Contribuir

### 🐛 Reportando Bugs

1. **Verifique se o bug já foi reportado** - Procure nas [Issues](https://github.com/felipeanexo/edsp-web-scrapper/issues) existentes
2. **Crie uma nova issue** - Use o template "[BUG]" para reportar bugs
3. **Forneça detalhes completos** - Inclua passos para reproduzir, screenshots e informações do sistema

### 💡 Sugerindo Melhorias

1. **Verifique se a funcionalidade já foi sugerida** - Procure nas [Issues](https://github.com/felipeanexo/edsp-web-scrapper/issues) existentes
2. **Crie uma nova issue** - Use o template "[FEATURE]" para sugerir melhorias
3. **Descreva detalhadamente** - Explique o problema e a solução proposta

### 🔧 Contribuindo com Código

#### Pré-requisitos
- Python 3.12+
- Poetry
- Git

#### Passos para Contribuir

1. **Fork o repositório**
   ```bash
   git clone https://github.com/seu-usuario/edsp-web-scrapper.git
   cd edsp-web-scrapper
   ```

2. **Configure o ambiente**
   ```bash
   poetry install
   poetry run playwright install
   ```

3. **Crie uma branch para sua feature**
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```

4. **Faça suas alterações**
   - Siga os padrões de código existentes
   - Adicione logs estruturados para novas funcionalidades
   - Inclua tratamento de erros robusto
   - Mantenha a arquitetura limpa

5. **Teste suas alterações**
   ```bash
   poetry run python main.py sample
   ```

6. **Commit suas mudanças**
   ```bash
   git add .
   git commit -m "feat: adiciona nova funcionalidade"
   ```

7. **Push para sua branch**
   ```bash
   git push origin feature/nova-funcionalidade
   ```

8. **Abra um Pull Request**
   - Use o template de PR
   - Descreva as mudanças detalhadamente
   - Inclua screenshots se aplicável

## Padrões de Código

### 🏗️ Arquitetura
- **Clean Architecture** - Mantenha a separação de responsabilidades
- **Domain Layer** - Lógica de negócio pura
- **Application Layer** - Casos de uso e serviços
- **Infrastructure Layer** - Preocupações externas

### 📝 Logs
- Use logs estruturados com contexto
- Inclua informações relevantes para debugging
- Mantenha consistência no formato

### 🐛 Tratamento de Erros
- Implemente tratamento robusto de erros
- Use try-catch apropriados
- Forneça mensagens de erro claras

### 📊 Dados
- Mantenha a estrutura de dados consistente
- Valide dados de entrada
- Documente novos campos

## Tipos de Contribuição

### 🐛 Bug Fixes
- Corrija bugs existentes
- Adicione testes se possível
- Documente a correção

### ✨ New Features
- Implemente novas funcionalidades
- Adicione documentação
- Inclua exemplos de uso

### 📚 Documentation
- Melhore a documentação
- Adicione exemplos
- Corrija erros de gramática

### 🎨 UI/UX Improvements
- Melhore a interface do dashboard
- Adicione animações ou transições
- Otimize para mobile

## Processo de Review

1. **Automated Checks** - CI/CD verificará seu código
2. **Code Review** - Mantenedores revisarão seu PR
3. **Testing** - Seu código será testado
4. **Merge** - Após aprovação, será mergeado

## Comunicação

- **Issues** - Para bugs e sugestões
- **Discussions** - Para perguntas e discussões
- **Pull Requests** - Para contribuições de código

## Agradecimentos

Obrigado por contribuir para melhorar a educação em São Paulo! 🎓

---

**Desenvolvido com ❤️ por Felipe Anexo** 