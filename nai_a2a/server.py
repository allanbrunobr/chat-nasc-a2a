"""
A2A Server implementation for NAI.

This server runs alongside the existing ADK-based API to provide A2A protocol support.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.routing import Mount
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv

from nai_a2a.agent_card import NAI_AGENT_CARD
from nai_a2a.executor import NAIAgentExecutor
from nai_a2a.session.postgres_store import PostgresTaskStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_a2a_app() -> FastAPI:
    """Create the A2A FastAPI application"""
    
    # Initialize components
    executor = NAIAgentExecutor()
    
    # Use PostgreSQL-backed task store for persistence
    use_postgres = os.getenv("A2A_USE_POSTGRES_STORE", "true").lower() == "true"
    
    if use_postgres:
        try:
            task_store = PostgresTaskStore()
            logger.info("Using PostgreSQL task store for A2A")
        except Exception as e:
            logger.warning(f"Failed to initialize PostgreSQL task store: {e}")
            logger.info("Falling back to in-memory task store")
            task_store = InMemoryTaskStore()
    else:
        task_store = InMemoryTaskStore()
        logger.info("Using in-memory task store for A2A")
    
    # Create request handler
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store
    )
    
    # Create A2A application
    a2a_app = A2AStarletteApplication(
        agent_card=NAI_AGENT_CARD,
        http_handler=handler
    )
    
    # Build the Starlette app
    starlette_app = a2a_app.build()
    
    # Create FastAPI app and mount the A2A app
    app = FastAPI(
        title="NAI A2A Server",
        description="A2A Protocol endpoint for NAI - SENAI's Intelligent Assistant",
        version="1.0.0"
    )
    
    # Mount the A2A Starlette app under the root path
    app.mount("/", starlette_app)
    
    # Add CORS middleware (matching the main API configuration)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom endpoints as separate FastAPI app
    health_app = FastAPI()
    
    @health_app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "protocol": "a2a",
            "agent": NAI_AGENT_CARD.name,
            "version": NAI_AGENT_CARD.version
        }
    
    @health_app.get("/info")
    async def info():
        """Info endpoint with basic info"""
        return {
            "name": NAI_AGENT_CARD.name,
            "description": NAI_AGENT_CARD.description,
            "protocol": "a2a",
            "endpoints": {
                "agent_card": "/.well-known/agent.json",
                "execute": "/execute",
                "tasks": "/tasks/{task_id}",
                "health": "/health"
            }
        }
    
    # Mount health app
    app.mount("/api", health_app)
    
    return app

# Create the app instance
app = create_a2a_app()

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("A2A_PORT", "8081"))
    
    logger.info(f"Starting NAI A2A server on port {port}")
    logger.info(f"Agent card available at: http://localhost:{port}/.well-known/agent.json")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )