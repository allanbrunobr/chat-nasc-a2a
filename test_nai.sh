#!/bin/bash
# Detailed NAI test script

BASE_URL="http://localhost:8080"
USER_ID="dd060639-cb4c-46a2-aac9-764a979b2d50"

echo "🧪 NAI Detailed Test"
echo "📍 Server: $BASE_URL"
echo "👤 User ID: $USER_ID"

echo -e "\n======================================"
echo "Test 1: Server Health Check"
echo "======================================"
curl -s "$BASE_URL/docs" | head -20

echo -e "\n\n======================================"
echo "Test 2: Simple Greeting"
echo "======================================"
curl -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Olá\"}]
  }" 2>&1

echo -e "\n\n======================================"
echo "Test 3: Profile Request"
echo "======================================"
curl -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Mostre meu perfil\"}]
  }" 2>&1

echo -e "\n\n======================================"
echo "Test 4: Create Profile"
echo "======================================"
curl -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Quero criar meu perfil\"}]
  }" 2>&1

echo -e "\n\n======================================"
echo "Test 5: Full Profile Creation"
echo "======================================"
curl -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Meu nome é João Silva, tenho 30 anos, sou formado em Engenharia de Software e trabalho como desenvolvedor há 5 anos\"}]
  }" 2>&1

echo -e "\n"