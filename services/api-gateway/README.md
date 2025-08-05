# API Gateway Service

## Overview

The API Gateway is the **single entry point** for all client requests in the Bkmrk'd Bookstore application. It provides centralized routing, authentication, rate limiting, caching, and monitoring for all microservices.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Client        │    │  API Gateway     │    │  Microservices      │
│   (Frontend)    │───▶│  (Port 8000)     │───▶│  (Ports 8001-8005)  │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Redis Cache     │
                       │  & Rate Limiting │
                       └──────────────────┘
```

## Features

### 🔐 **Authentication & Authorization**
- JWT token validation
- Centralized user authentication
- Role-based access control
- Token refresh handling

### 🚦 **Rate Limiting**
- Per-endpoint rate limits
- IP-based throttling
- Configurable limits per service
- Rate limit headers in responses

### 💾 **Caching**
- Redis-based response caching
- TTL-based cache invalidation
- Cache key generation strategies
- Cache warming for popular endpoints

### 🔄 **Request Routing**
- Service discovery and routing
- Load balancing across service instances
- Request/response transformation
- Error handling and retry logic

### 📊 **Monitoring & Analytics**
- Request/response logging
- Performance metrics collection
- Service health monitoring
- Error tracking and alerting

### 🛡️ **Security**
- CORS configuration
- Trusted host validation
- Request sanitization
- Security headers

## Service Endpoints

### Health Check
- `GET /health` - Gateway and service health status

### Generic Routing
- `POST /api/gateway/route` - Generic service routing

### Book Management
- `GET /api/books` - Get books with filters
- `GET /api/books/{id}` - Get book by ID
- `GET /api/search` - Search books

### Recommendations
- `POST /api/recommendations` - Get recommendations
- `GET /api/recommendations/wishlist` - Wishlist recommendations
- `GET /api/recommendations/trending` - Trending recommendations

### User Management
- `GET /api/users/me` - Get current user
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Cart Operations
- `GET /api/cart` - Get user cart
- `POST /api/cart/items` - Add to cart
- `PUT /api/cart/items/{id}` - Update cart item
- `DELETE /api/cart/items/{id}` - Remove from cart

### ML/AI Services
- `POST /api/ml/embed` - Text embedding
- `POST /api/ml/search` - Vector search

### Analytics
- `GET /api/analytics/metrics` - Get analytics metrics

## Environment Variables

```bash
# Service URLs
BACKEND_SERVICE_URL=http://backend-service:8001
RECOMMENDATION_SERVICE_URL=http://recommendation-engine:8002
ML_SERVICE_URL=http://ml-service:8003
OBSERVABILITY_SERVICE_URL=http://observability-service:8004
ETL_SERVICE_URL=http://etl-pipeline:8005

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=bookstore_redis_pass

# Security
ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=*

# Logging
LOG_LEVEL=INFO
```

## Rate Limits

| Endpoint | Limit | Description |
|----------|-------|-------------|
| `/health` | 100/min | Health check |
| `/api/books` | 1000/min | Book retrieval |
| `/api/recommendations` | 500/min | Recommendations |
| `/api/ml/*` | 200/min | ML operations |
| `/api/analytics/*` | 100/min | Analytics |
| `/api/cart/*` | 100/min | Cart operations |
| `/api/users/*` | 100/min | User operations |

## Caching Strategy

### Cache Keys
- Format: `gateway:{service}:{endpoint}:{method}:{hash}`
- TTL: 5 minutes (configurable)
- Invalidation: Manual or TTL-based

### Cached Endpoints
- `GET /api/books` (with query parameters)
- `GET /api/books/{id}`
- `GET /api/search`
- `GET /api/recommendations/trending`

## Error Handling

### HTTP Status Codes
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (service/endpoint not found)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error (gateway error)
- `502` - Bad Gateway (service unavailable)
- `504` - Gateway Timeout (service timeout)

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "service": "api-gateway",
  "timestamp": 1640995200.0
}
```

## Performance Optimizations

### Connection Pooling
- HTTPX async client with connection pooling
- Configurable pool size and timeouts
- Connection reuse across requests

### Response Streaming
- Large response streaming support
- Chunked transfer encoding
- Memory-efficient processing

### Load Balancing
- Round-robin service routing
- Health check-based routing
- Circuit breaker pattern (planned)

## Monitoring & Observability

### Metrics
- Request count per endpoint
- Response time percentiles
- Error rate tracking
- Cache hit/miss ratios

### Logging
- Structured JSON logging
- Request/response correlation IDs
- Service dependency tracking
- Performance bottleneck identification

### Health Checks
- Gateway health status
- Service dependency health
- Redis connection status
- Overall system health

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/
```

### Docker Development
```bash
# Build and run
docker-compose up api-gateway

# View logs
docker-compose logs -f api-gateway
```

### Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/
```

## Deployment

### Docker
```bash
# Build image
docker build -t bookstore-api-gateway .

# Run container
docker run -p 8000:8000 bookstore-api-gateway
```

### Kubernetes
```bash
# Apply deployment
kubectl apply -f k8s/base/api-gateway-deployment.yaml

# Check status
kubectl get pods -l app=api-gateway
```

## Security Considerations

### Authentication
- JWT token validation with backend service
- Token refresh mechanism
- Secure token storage

### Authorization
- Role-based access control
- Endpoint-level permissions
- User context validation

### Input Validation
- Request parameter validation
- SQL injection prevention
- XSS protection

### Rate Limiting
- IP-based rate limiting
- User-based rate limiting
- Burst protection

## Troubleshooting

### Common Issues

1. **Service Unavailable (503)**
   - Check if target service is running
   - Verify service URL configuration
   - Check network connectivity

2. **Rate Limit Exceeded (429)**
   - Reduce request frequency
   - Implement client-side retry logic
   - Contact administrator for limit increase

3. **Authentication Failed (401)**
   - Verify JWT token validity
   - Check token expiration
   - Ensure proper Authorization header

4. **Cache Issues**
   - Check Redis connection
   - Verify cache key generation
   - Monitor cache hit/miss ratios

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
uvicorn app.main:app --log-level debug
```

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Submit pull request

## License

This project is licensed under the MIT License. 