# Configuração Meta Pixels - Prosegur CNV

## Configuração dos Secrets

⭐ **APENAS O PIXEL ID É NECESSÁRIO!**  
Não precisa de tokens de acesso. O tracking é feito via JavaScript no navegador.

Configure os seguintes secrets no ambiente:

```
META_PIXEL_1_ID = 123456789012345
META_PIXEL_2_ID = 123456789012346
META_PIXEL_3_ID = 123456789012347
META_PIXEL_4_ID = 123456789012348
META_PIXEL_5_ID = 123456789012349
META_PIXEL_6_ID = 123456789012350
```

## Como Obter o Pixel ID

1. **Acesse o Gerenciador de Eventos da Meta**
   - Entre em https://business.facebook.com/events_manager
   - Selecione sua conta publicitária

2. **Encontre seu Pixel**
   - Vá em "Fontes de Dados" > "Pixels"
   - Clique no pixel que você quer usar

3. **Copie o Pixel ID**
   - O ID aparece no topo da página (número de 15 dígitos)
   - Exemplo: `123456789012345`

4. **Configure no Ambiente**
   - Adicione o secret: `META_PIXEL_1_ID = SEU_PIXEL_ID`
   - Para múltiplos pixels, use META_PIXEL_2_ID, META_PIXEL_3_ID, etc.

## Eventos Enviados

O sistema envia automaticamente eventos de **Purchase** para todos os pixels configurados quando:

1. **Pagamento aprovado em /pagamento** (CNV R$ 73,40)
2. **Pagamento CNV aprovado em /finalizar** (CNV R$ 82,10)

### Dados Enviados (Hasheados)
- Email do cliente
- Telefone do cliente  
- CPF (como external_id)
- Nome completo
- Cidade e estado
- CEP
- Valor da compra
- ID da transação
- Método de pagamento

## Teste da Configuração

Acesse `/admin/meta-pixels` para:
- Ver status dos pixels configurados
- Testar conexão com a API da Meta
- Verificar se os eventos estão sendo enviados

## Logs

Os eventos são registrados no log da aplicação:
- `Conversão enviada com sucesso para X/Y pixels`
- `Erro ao enviar conversão para Meta Pixels: [erro]`

## Monitoramento

No Gerenciador de Eventos da Meta você pode ver:
- Eventos recebidos em tempo real
- Taxa de correspondência dos dados
- Qualidade dos eventos
- Métricas de conversão