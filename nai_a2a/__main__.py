"""
A2A server entry point for NAI.

Allows running the A2A server as a module: python -m nai_a2a
"""

import os
import logging
import uvicorn
from nai_a2a.server import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("A2A_PORT", "8082"))
    
    logger.info(f"Starting NAI A2A server on port {port}")
    logger.info(f"Agent card available at: http://localhost:{port}/.well-known/agent.json")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )