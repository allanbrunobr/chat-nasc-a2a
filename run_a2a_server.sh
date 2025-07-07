#!/bin/bash
# Run A2A server with environment variables

cd "/Users/bruno/0 - AI projects/Xertica - AI/nai-api-a2a"

# Export environment variables
export USER_PROFILE_URL="https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/get-user-profile-parallelism"
export DB_USER=postgres
export DB_PASSWORD='J3xk(D[l[RMfK.nT'
export DB_HOST=34.28.37.68
export DB_PORT=5432
export DB_NAME=vcc-db-v2
export A2A_PORT=8082

# Add current directory to Python path
export PYTHONPATH="/Users/bruno/0 - AI projects/Xertica - AI/nai-api-a2a:$PYTHONPATH"

# Run the server
python nai_a2a/server.py