"""
Exemplos simples de como adicionar tracing com Phoenix/OpenTelemetry
"""
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

# Obter o tracer uma vez para o módulo
tracer = trace.get_tracer(__name__)

# EXEMPLO 1: Trace simples com decorator
@tracer.start_as_current_span("calcular_desconto")
def calcular_desconto(preco: float, percentual: float) -> float:
    """Exemplo simples com decorator"""
    # O span é criado automaticamente
    desconto = preco * (percentual / 100)
    return preco - desconto

# EXEMPLO 2: Trace com atributos
def buscar_usuario(user_id: str):
    """Exemplo com atributos no span"""
    with tracer.start_as_current_span("buscar_usuario") as span:
        # Adicionar informações úteis ao span
        span.set_attribute("user.id", user_id)
        span.set_attribute("database.name", "users_db")
        
        # Simular busca no banco
        time.sleep(0.1)
        
        # Adicionar eventos
        span.add_event("usuario_encontrado", {
            "user.type": "premium",
            "user.active": True
        })
        
        return {"id": user_id, "nome": "João", "tipo": "premium"}

# EXEMPLO 3: Trace com tratamento de erro
def processar_pagamento(valor: float, cartao: str):
    """Exemplo com tratamento de erro"""
    with tracer.start_as_current_span("processar_pagamento") as span:
        span.set_attribute("payment.amount", valor)
        span.set_attribute("payment.method", "credit_card")
        
        try:
            if valor > 1000:
                raise ValueError("Valor acima do limite")
            
            # Processar pagamento
            time.sleep(0.2)
            
            span.set_status(Status(StatusCode.OK))
            span.add_event("pagamento_aprovado")
            return {"status": "aprovado", "transacao_id": "12345"}
            
        except Exception as e:
            # Registrar erro no span
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.add_event("pagamento_falhou", {"erro": str(e)})
            raise

# EXEMPLO 4: Traces aninhados
def processar_pedido(pedido_id: str):
    """Exemplo com múltiplos spans aninhados"""
    with tracer.start_as_current_span("processar_pedido") as span:
        span.set_attribute("order.id", pedido_id)
        
        # Passo 1: Validar pedido
        with tracer.start_as_current_span("validar_pedido") as validation_span:
            validation_span.set_attribute("validation.type", "complete")
            time.sleep(0.05)
            validation_span.add_event("pedido_valido")
        
        # Passo 2: Calcular preço
        with tracer.start_as_current_span("calcular_preco") as price_span:
            preco_total = 150.00
            price_span.set_attribute("price.total", preco_total)
            price_span.set_attribute("price.currency", "BRL")
            time.sleep(0.05)
        
        # Passo 3: Processar pagamento
        with tracer.start_as_current_span("processar_pagamento_pedido") as payment_span:
            payment_span.set_attribute("payment.amount", preco_total)
            try:
                time.sleep(0.1)
                payment_span.add_event("pagamento_processado")
            except Exception as e:
                payment_span.record_exception(e)
                raise
        
        span.set_status(Status(StatusCode.OK))
        return {"pedido_id": pedido_id, "status": "processado"}

# EXEMPLO 5: Trace assíncrono
import asyncio

async def buscar_dados_async(fonte: str):
    """Exemplo com função assíncrona"""
    with tracer.start_as_current_span("buscar_dados_async") as span:
        span.set_attribute("data.source", fonte)
        
        # Simular operação assíncrona
        await asyncio.sleep(0.1)
        
        dados = {"fonte": fonte, "registros": 100}
        span.set_attribute("data.count", dados["registros"])
        
        return dados

# EXEMPLO 6: Adicionar trace a código existente facilmente
def sua_funcao_existente(param1, param2):
    """Como adicionar trace a uma função que já existe"""
    # Adicione apenas estas 2 linhas no início:
    with tracer.start_as_current_span("sua_funcao_existente") as span:
        span.set_attribute("param1", param1)
        
        # Todo o código existente continua igual
        resultado = param1 + param2
        
        # Opcional: adicionar mais informações antes de retornar
        span.set_attribute("resultado", resultado)
        return resultado

# EXEMPLO 7: Trace para chamadas HTTP
import requests

def chamar_api_externa(endpoint: str):
    """Exemplo de trace para requisições HTTP"""
    with tracer.start_as_current_span("chamar_api_externa") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", endpoint)
        
        try:
            response = requests.get(endpoint)
            
            # Adicionar informações da resposta
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_size", len(response.content))
            
            if response.status_code == 200:
                span.set_status(Status(StatusCode.OK))
                return response.json()
            else:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                return None
                
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            raise

# DICAS IMPORTANTES:
# 1. Use nomes descritivos para os spans
# 2. Adicione atributos relevantes (user_id, request_id, etc)
# 3. Use add_event() para marcar momentos importantes
# 4. Sempre trate erros com record_exception()
# 5. Defina o status do span (OK ou ERROR)
# 6. Não crie spans para operações muito pequenas
# 7. Para ver os traces, acesse: http://localhost:6006