#!/bin/bash

echo "🔍 Testando Cloud Function get-empresa-profile-parallelism"
echo "=================================================="

USER_ID="cm499i7ue0003lkqhs7a6e76h"
URL="https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/get-empresa-profile-parallelism"

echo "📍 URL: $URL"
echo "👤 User ID: $USER_ID"
echo ""

echo "🚀 Fazendo requisição..."
echo ""

# Fazer requisição e salvar resposta
RESPONSE=$(curl -s -w "\n\nHTTP_STATUS:%{http_code}" "$URL?user_id=$USER_ID")

# Extrair status HTTP e corpo da resposta
HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "📊 Status HTTP: $HTTP_STATUS"
echo ""
echo "📋 Resposta:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo ""
echo "✅ Teste concluído"