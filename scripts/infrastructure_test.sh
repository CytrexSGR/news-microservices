#!/bin/bash

echo "=== Infrastructure Health Checks ==="
echo ""

# PostgreSQL
echo -n "Testing PostgreSQL... "
pg_result=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c "SELECT 1" 2>/dev/null | xargs)
if [ "$pg_result" == "1" ]; then
    echo "✅ PASS"
    
    # Get stats
    feed_count=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM feeds" 2>/dev/null | xargs)
    article_count=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM articles" 2>/dev/null | xargs)
    analysis_count=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM public.article_analysis" 2>/dev/null | xargs)
    
    echo "  - Feeds: $feed_count"
    echo "  - Articles: $article_count"
    echo "  - Analyses: $analysis_count"
else
    echo "❌ FAIL"
fi
echo ""

# Redis
echo -n "Testing Redis... "
redis_result=$(docker exec -i redis redis-cli -a redis_secret_2024 --no-auth-warning PING 2>/dev/null)
if [ "$redis_result" == "PONG" ]; then
    echo "✅ PASS"
    
    # Get stats
    keys=$(docker exec -i redis redis-cli -a redis_secret_2024 --no-auth-warning DBSIZE 2>/dev/null | cut -d: -f2 | xargs)
    memory=$(docker exec -i redis redis-cli -a redis_secret_2024 --no-auth-warning INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | xargs)
    
    echo "  - Keys: $keys"
    echo "  - Memory: $memory"
else
    echo "❌ FAIL"
fi
echo ""

# RabbitMQ
echo -n "Testing RabbitMQ... "
rabbitmq_result=$(curl -s -u guest:guest http://localhost:15672/api/overview 2>&1 | jq -r '.rabbitmq_version' 2>/dev/null)
if [ -n "$rabbitmq_result" ] && [ "$rabbitmq_result" != "null" ]; then
    echo "✅ PASS (v$rabbitmq_result)"
    
    # Get stats
    queues=$(curl -s -u guest:guest http://localhost:15672/api/queues 2>&1 | jq length 2>/dev/null)
    echo "  - Queues: $queues"
else
    echo "❌ FAIL"
fi
echo ""

# Neo4j
echo -n "Testing Neo4j... "
neo4j_result=$(curl -s http://localhost:7474/ 2>&1 | grep -o "neo4j" | head -1)
if [ "$neo4j_result" == "neo4j" ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi
