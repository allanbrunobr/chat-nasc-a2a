"""
PostgreSQL-based TaskStore implementation for A2A.

This provides persistent task storage compatible with the existing NAI database.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from a2a.server.tasks import TaskStore
from a2a.types import Task, TaskState
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class PostgresTaskStore(TaskStore):
    """
    PostgreSQL-backed task store for A2A protocol.
    
    Stores tasks in a dedicated table while maintaining compatibility
    with the existing session management.
    """
    
    def __init__(self):
        """Initialize the PostgreSQL connection pool"""
        # Database configuration from environment
        db_config = {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD")
        }
        
        # Create connection pool
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **db_config
        )
        
        # Create tasks table if it doesn't exist
        self._create_table()
    
    def _create_table(self):
        """Create the a2a_tasks table if it doesn't exist"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS a2a_tasks (
                        task_id VARCHAR(255) PRIMARY KEY,
                        state VARCHAR(50) NOT NULL,
                        request JSONB NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        result JSONB,
                        error TEXT
                    )
                """)
                
                # Create index on state for efficient querying
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_a2a_tasks_state 
                    ON a2a_tasks(state)
                """)
                
                # Create index on created_at for cleanup
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_a2a_tasks_created 
                    ON a2a_tasks(created_at)
                """)
                
                conn.commit()
                logger.info("A2A tasks table initialized successfully")
        except Exception as e:
            logger.error(f"Error creating tasks table: {e}")
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)
    
    async def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT task_id, state, request, metadata, result, error,
                           created_at, updated_at
                    FROM a2a_tasks
                    WHERE task_id = %s
                """, (task_id,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                # Convert database row to Task object
                task = Task(
                    id=row['task_id'],
                    state=TaskState(row['state']),
                    request=row['request'],  # Already JSONB
                    metadata=row['metadata'] or {}
                )
                
                if row['result']:
                    task.result = row['result']
                if row['error']:
                    task.error = row['error']
                
                return task
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
            return None
        finally:
            self.pool.putconn(conn)
    
    async def save(self, task: Task) -> None:
        """Store or update a task"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Serialize task data
                # A2A tasks don't have request attribute, use history instead
                request_data = {}
                if hasattr(task, 'request'):
                    request_data = task.request
                elif hasattr(task, 'history') and task.history:
                    # Convert history to a simple request representation
                    request_data = {
                        "messages": [{"role": msg.role, "content": str(msg)} for msg in task.history]
                    }
                request_json = json.dumps(request_data) if request_data else '{}'
                
                # Handle metadata - A2A tasks might have it in status
                metadata = {}
                if hasattr(task, 'metadata') and task.metadata:
                    metadata = task.metadata
                elif hasattr(task, 'status') and hasattr(task.status, 'metadata') and task.status.metadata:
                    metadata = task.status.metadata
                metadata_json = json.dumps(metadata) if metadata else None
                
                result_json = json.dumps(task.result) if hasattr(task, 'result') and task.result else None
                error_text = task.error if hasattr(task, 'error') else None
                
                # Upsert the task
                cur.execute("""
                    INSERT INTO a2a_tasks (task_id, state, request, metadata, result, error, updated_at)
                    VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (task_id) DO UPDATE SET
                        state = EXCLUDED.state,
                        request = EXCLUDED.request,
                        metadata = EXCLUDED.metadata,
                        result = EXCLUDED.result,
                        error = EXCLUDED.error,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    task.id,
                    task.status.state.value if hasattr(task, 'status') and hasattr(task.status, 'state') else 'unknown',
                    request_json,
                    metadata_json,
                    result_json,
                    error_text
                ))
                
                conn.commit()
                logger.debug(f"Task {task.id} stored successfully")
        except Exception as e:
            logger.error(f"Error storing task {task.id}: {e}")
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)
    
    async def delete(self, task_id: str) -> None:
        """Delete a task"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM a2a_tasks WHERE task_id = %s", (task_id,))
                conn.commit()
                logger.debug(f"Task {task_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            conn.rollback()
        finally:
            self.pool.putconn(conn)
    
    async def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        Clean up tasks older than specified days.
        
        Returns the number of tasks deleted.
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM a2a_tasks
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    AND state IN ('completed', 'failed', 'cancelled')
                """, (days,))
                
                deleted_count = cur.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old tasks")
                return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")
            conn.rollback()
            return 0
        finally:
            self.pool.putconn(conn)
    
    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'pool'):
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")