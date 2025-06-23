# Deploy para Heroku - Conselheiro Tutelar System

## Configuração Rápida

### 1. Preparar Repositório Git
```bash
git init
git add .
git commit -m "Initial commit - Conselheiro Tutelar System"
```

### 2. Criar App no Heroku
```bash
heroku create seu-app-name
heroku addons:create heroku-postgresql:essential-0
```

### 3. Configurar Variáveis de Ambiente
```bash
# Obrigatórias
heroku config:set FLASK_ENV=production
heroku config:set SESSION_SECRET=$(openssl rand -hex 32)
heroku config:set FOR4PAYMENTS_SECRET_KEY=sua-chave-for4payments

# Opcionais
heroku config:set SMSDEV_API_KEY=sua-chave-sms
heroku config:set OPENAI_API_KEY=sua-chave-openai
heroku config:set META_PIXEL_1_ID=seu-pixel-id
```

### 4. Deploy
```bash
git push heroku main
```

## Arquivos de Configuração

### ✅ Procfile
- Configurado com Gunicorn para produção
- 4 workers para alta disponibilidade
- Otimizado para Heroku

### ✅ requirements.txt
- Dependências limpas e versionadas
- Gunicorn incluído para produção
- Todas as bibliotecas necessárias

### ✅ runtime.txt
- Python 3.11.9 (versão estável)

### ✅ app.json
- Configuração automática de addons
- Variáveis de ambiente documentadas
- Scripts de pós-deploy

## Funcionalidades Incluídas

### Sistema Completo
- ✅ Formulário com validação CPF e auto-preenchimento
- ✅ Sistema de exames e avaliação psicológica  
- ✅ Pagamentos PIX com QR codes autênticos
- ✅ Analytics em tempo real com Meta Pixels
- ✅ Proteção mobile e anti-cloning
- ✅ Sistema de ranking e aprovação
- ✅ Chat e agendamento integrados

### APIs Integradas
- ✅ For4Payments para PIX
- ✅ CPF API para dados reais
- ✅ OpenAI para localização
- ✅ Meta Pixels para conversão
- ✅ SMS (opcional)

### Otimizações Heroku
- ✅ Gerenciamento de memória
- ✅ Cache inteligente
- ✅ Pool de conexões otimizado
- ✅ Rate limiting removido
- ✅ Logs otimizados

## Monitoramento

### Métricas Disponíveis
- Usuários ativos em tempo real
- Conversões de pagamento
- Performance de rotas
- Uso de memória
- Erros e healthcheck

### Logs
```bash
heroku logs --tail
heroku logs --source app
```

### Escalabilidade
```bash
heroku ps:scale web=2  # Escalar para 2 dynos
heroku addons:upgrade heroku-postgresql:standard-0  # Upgrade database
```

## Segurança

### Variáveis Protegidas
- SESSION_SECRET: Gerado automaticamente
- API Keys: Configuradas via environment
- Database: SSL obrigatório

### Proteções Ativas
- Mobile-only access
- Request rate monitoring
- Session cleanup automático
- Error handling robusto

## Troubleshooting

### Problemas Comuns
1. **Database não conecta**: Verificar DATABASE_URL
2. **Pagamentos falham**: Verificar FOR4PAYMENTS_SECRET_KEY
3. **App não inicia**: Verificar logs com `heroku logs`
4. **Memória alta**: App tem otimizações automáticas

### Reset Completo
```bash
heroku pg:reset DATABASE_URL --confirm seu-app-name
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Contato
Sistema desenvolvido para processo seletivo de Conselheiro Tutelar com integração completa de pagamentos PIX e analytics avançadas.