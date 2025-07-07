#!/usr/bin/env python3
"""
Start both ADK and A2A servers for NAI.

This script runs both servers in parallel, allowing the system to handle
both ADK (legacy) and A2A (new) protocols simultaneously.
"""

import os
import sys
import subprocess
import signal
import time
from multiprocessing import Process
import logging

# Script now runs from nai-api-a2a directory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def kill_existing_processes():
    """Kill any existing processes on our ports"""
    ports = [8080, 8082]
    for port in ports:
        try:
            # Find process using the port
            result = subprocess.run(
                ["lsof", "-t", f"-i:{port}"], 
                capture_output=True, 
                text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    logger.info(f"Killing process {pid} on port {port}")
                    subprocess.run(["kill", "-9", pid])
                time.sleep(1)  # Give it time to release the port
        except Exception as e:
            logger.debug(f"No process found on port {port}: {e}")

def run_adk_server():
    """Run the ADK server on port 8080"""
    logger.info("Starting ADK server on port 8080...")
    # Get nai-api directory (sibling directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    nai_api_dir = os.path.join(os.path.dirname(current_dir), "nai-api")
    
    logger.info(f"Running ADK from: {nai_api_dir}")
    
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "api.main:app", 
        "--host", "0.0.0.0",
        "--port", "8080",
        "--reload"
    ], cwd=nai_api_dir)

def run_a2a_server():
    """Run the A2A server on port 8082"""
    logger.info("Starting A2A server on port 8082...")
    
    # Current directory is already nai-api-a2a
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Known a2a module location
    a2a_module_path = "/opt/anaconda3/lib/python3.12/site-packages"
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{current_dir}:{a2a_module_path}"
    env["A2A_PORT"] = "8082"
    
    logger.info(f"Running A2A from: {current_dir}")
    logger.info(f"PYTHONPATH: {env['PYTHONPATH']}")
    
    # Run the A2A server
    subprocess.run([
        sys.executable, "-m", 
        "nai_a2a"
    ], cwd=current_dir, env=env)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutting down servers...")
    sys.exit(0)

def main():
    """Main function to start both servers"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║           NAI - SENAI's Intelligent Assistant         ║
    ║                  Hybrid Mode (ADK + A2A)              ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Kill any existing processes first
    logger.info("Checking for existing processes...")
    kill_existing_processes()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create processes for each server
    adk_process = Process(target=run_adk_server, name="ADK-Server")
    a2a_process = Process(target=run_a2a_server, name="A2A-Server")
    
    try:
        # Start both servers
        adk_process.start()
        time.sleep(2)  # Give ADK server time to start
        a2a_process.start()
        
        logger.info("Both servers started successfully!")
        print("\n" + "="*60)
        print("🚀 NAI is running in hybrid mode:")
        print(f"   • ADK API: http://localhost:8080")
        print(f"   • A2A API: http://localhost:8082")
        print(f"   • A2A Agent Card: http://localhost:8082/.well-known/agent.json")
        print("="*60 + "\n")
        print("Press Ctrl+C to stop both servers")
        
        # Wait for both processes
        adk_process.join()
        a2a_process.join()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        # Ensure both processes are terminated
        if adk_process.is_alive():
            adk_process.terminate()
            adk_process.join()
        if a2a_process.is_alive():
            a2a_process.terminate()
            a2a_process.join()
        
        logger.info("All servers stopped")

if __name__ == "__main__":
    main()