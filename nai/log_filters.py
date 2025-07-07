"""
Custom log filters to clean up output
"""
import logging

class IgnoreContextDetachErrors(logging.Filter):
    """
    Filter to ignore specific OpenTelemetry context detach errors
    that are harmless but noisy
    """
    def filter(self, record):
        # Ignore "Failed to detach context" errors
        if record.getMessage().startswith("Failed to detach context"):
            return False
        
        # Ignore "was created in a different Context" errors
        if "was created in a different Context" in record.getMessage():
            return False
            
        # Allow all other logs
        return True

def apply_log_filters():
    """
    Apply custom filters to clean up logs
    """
    # Add filter to OpenTelemetry context logger
    otel_logger = logging.getLogger("opentelemetry.context")
    otel_logger.addFilter(IgnoreContextDetachErrors())
    
    # Also apply to OpenInference logger
    oi_logger = logging.getLogger("openinference.instrumentation.google_adk")
    oi_logger.addFilter(IgnoreContextDetachErrors())