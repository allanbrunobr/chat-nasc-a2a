"""
Custom exceptions for A2A NAI implementation.

These exceptions provide specific error types for better error handling
and recovery strategies.
"""

from typing import Optional, Dict, Any


class NAIError(Exception):
    """Base exception for all NAI-specific errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UserNotFoundException(NAIError):
    """Raised when a user profile cannot be found"""
    
    def __init__(self, user_id: str):
        super().__init__(
            f"Perfil não encontrado para o usuário: {user_id}",
            {"user_id": user_id, "error_type": "user_not_found"}
        )
        self.user_id = user_id


class ProfileIncompleteError(NAIError):
    """Raised when user profile is incomplete for requested operation"""
    
    def __init__(self, missing_fields: list[str], operation: str, user_id: Optional[str] = None):
        super().__init__(
            f"Perfil incompleto para {operation}. Campos faltando: {', '.join(missing_fields)}",
            {
                "missing_fields": missing_fields,
                "operation": operation,
                "user_id": user_id,
                "error_type": "profile_incomplete"
            }
        )
        self.missing_fields = missing_fields
        self.operation = operation
        self.user_id = user_id


class ValidationError(NAIError):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Erro de validação: {message}",
            {
                "validation_error": message,
                "error_type": "validation_error",
                **(details or {})
            }
        )


class ExternalAPIError(NAIError):
    """Raised when external API calls fail"""
    
    def __init__(self, service: str, status_code: Optional[int] = None, 
                 response_text: Optional[str] = None, error_type: Optional[str] = None):
        message = f"Erro ao comunicar com serviço externo: {service}"
        if status_code:
            message += f" (Status: {status_code})"
        elif error_type:
            message += f" ({error_type})"
            
        super().__init__(
            message,
            {
                "service": service,
                "status_code": status_code,
                "response": response_text,
                "error_type": error_type or "external_api_error"
            }
        )
        self.service = service
        self.status_code = status_code
        self.response_text = response_text
        self.error_type = error_type


class DatabaseConnectionError(NAIError):
    """Raised when database operations fail"""
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None):
        super().__init__(
            f"Erro de banco de dados durante: {operation}",
            {
                "operation": operation,
                "original_error": str(original_error) if original_error else None,
                "error_type": "database_error"
            }
        )
        self.operation = operation
        self.original_error = original_error


class SkillNotFoundError(NAIError):
    """Raised when requested skill is not available"""
    
    def __init__(self, skill_name: str):
        super().__init__(
            f"Habilidade não encontrada: {skill_name}",
            {"skill_name": skill_name, "error_type": "skill_not_found"}
        )
        self.skill_name = skill_name


class AuthenticationError(NAIError):
    """Raised when authentication fails"""
    
    def __init__(self, reason: str = "Invalid credentials"):
        super().__init__(
            f"Falha na autenticação: {reason}",
            {"reason": reason, "error_type": "authentication_error"}
        )


class AuthorizationError(NAIError):
    """Raised when user lacks permission for requested operation"""
    
    def __init__(self, operation: str, required_permission: Optional[str] = None):
        message = f"Sem permissão para: {operation}"
        if required_permission:
            message += f" (Requer: {required_permission})"
            
        super().__init__(
            message,
            {
                "operation": operation,
                "required_permission": required_permission,
                "error_type": "authorization_error"
            }
        )
        self.operation = operation
        self.required_permission = required_permission


class RateLimitExceededError(NAIError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, limit: int, window: str, retry_after: Optional[int] = None):
        message = f"Limite de requisições excedido: {limit} por {window}"
        if retry_after:
            message += f". Tente novamente em {retry_after} segundos"
            
        super().__init__(
            message,
            {
                "limit": limit,
                "window": window,
                "retry_after": retry_after,
                "error_type": "rate_limit_exceeded"
            }
        )
        self.limit = limit
        self.window = window
        self.retry_after = retry_after