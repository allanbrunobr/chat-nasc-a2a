#!/bin/bash

echo "🚀 Starting Phoenix LLM Observability..."

# Start Phoenix
docker-compose -f docker-compose.phoenix.yml up -d

# Wait for Phoenix to be ready
echo "⏳ Waiting for Phoenix to start..."
until curl -f http://localhost:6006/health > /dev/null 2>&1; do
  sleep 2
done

echo "✅ Phoenix is running!"
echo "📊 Dashboard available at: http://localhost:6006"
echo ""
echo "🔗 Endpoints:"
echo "   - UI: http://localhost:6006"
echo "   - OTLP gRPC: localhost:4317"
echo "   - OTLP HTTP: localhost:4318"