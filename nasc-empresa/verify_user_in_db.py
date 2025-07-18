#!/usr/bin/env python3
"""
Script para verificar se o user_id existe no banco e tem empresa associada
"""
import psycopg2
from datetime import datetime

# Configurações do banco (mesmas da cloud function)
DB_HOST = "34.28.37.68"
DB_PORT = "5432"
DB_NAME = "vcc-db-v2"
DB_USER = "postgres"
DB_PASSWORD = "J3xk(D[l[RMfK.nT"

# User ID para verificar
USER_ID = "bf76228e-30cb-496d-8cb9-c26899abf318"

print("🔍 Verificando user_id no banco de dados")
print(f"📊 Banco: {DB_NAME} em {DB_HOST}")
print(f"👤 User ID: {USER_ID}")
print("=" * 60)

try:
    # Conectar ao banco
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # 1. Verificar se o usuário existe
    print("\n1️⃣ Verificando se o usuário existe...")
    cursor.execute("""
        SELECT id, email, role, "companyId", active, "createdAt"
        FROM "User"
        WHERE id = %s
    """, (USER_ID,))
    
    user = cursor.fetchone()
    if user:
        print(f"✅ Usuário encontrado!")
        print(f"   Email: {user[1]}")
        print(f"   Role: {user[2]}")
        print(f"   Company ID: {user[3]}")
        print(f"   Ativo: {user[4]}")
        print(f"   Criado em: {user[5]}")
        
        # 2. Se tem company_id, buscar dados da empresa
        if user[3]:  # company_id
            print(f"\n2️⃣ Buscando dados da empresa (ID: {user[3]})...")
            cursor.execute("""
                SELECT id, "companyName", "businessName", "documentNumber", 
                       active, city, state, "phoneNumber"
                FROM "Company"
                WHERE id = %s
            """, (user[3],))
            
            company = cursor.fetchone()
            if company:
                print(f"✅ Empresa encontrada!")
                print(f"   Nome: {company[1]}")
                print(f"   Razão Social: {company[2]}")
                print(f"   CNPJ: {company[3]}")
                print(f"   Ativa: {company[4]}")
                print(f"   Cidade: {company[5]}, {company[6]}")
                print(f"   Telefone: {company[7]}")
            else:
                print(f"❌ Empresa com ID {user[3]} não encontrada!")
                
        # 3. Executar a query exata da cloud function
        print(f"\n3️⃣ Executando query exata da cloud function...")
        cursor.execute("""
            SELECT
                u.id as user_id,
                u.email as owner_email,
                u."corporateEmail",
                u.role,
                c.id as company_id,
                c."companyName",
                c."documentNumber"
            FROM "User" u
            INNER JOIN "Company" c ON u."companyId" = c.id
            WHERE u.role = 'EMPRESA'
                AND u.id = %s
                AND u.active = true
        """, (USER_ID,))
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Query da cloud function retornou dados!")
            print(f"   Company Name: {result[5]}")
            print(f"   CNPJ: {result[6]}")
        else:
            print(f"❌ Query da cloud function NÃO retornou dados!")
            print(f"   Possíveis razões:")
            print(f"   - Role não é 'EMPRESA' (atual: {user[2]})")
            print(f"   - Usuário não está ativo (atual: {user[4]})")
            print(f"   - Company ID é NULL (atual: {user[3]})")
            
    else:
        print(f"❌ Usuário com ID {USER_ID} não encontrado no banco!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Erro ao conectar no banco: {str(e)}")
    
print("\n" + "=" * 60)
print("✅ Verificação concluída")