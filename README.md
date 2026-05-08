# Ecommerce Microservices

A distributed ecommerce backend built with an event-driven microservices architecture. Handle product listings, customer orders, real-time analytics, anomaly detection, and system health monitoring â€” all across independently deployable services.

# 🚀 Tech Stack

- Python
- Flask / Connexion (OpenAPI)
- Apache Kafka (pykafka)
- SQLAlchemy
- MySQL
- SQLite
- Docker
- RESTful API design

# ðŸ— Architecture

The application follows an **event-driven microservices architecture**, where each service has a single responsibility and communicates asynchronously through Apache Kafka. Services are containerized using Docker and expose RESTful endpoints defined via OpenAPI specs.

All services support environment-aware configuration, loading separate config files for dev and test environments.

# ðŸ“¦ Services

## ðŸ“¥ Receiver (Port 8080)
The API gateway and entry point for all incoming requests. Accepts HTTP requests to create products and place orders, assigns trace IDs, and publishes events to Kafka for downstream processing.

## ðŸ—„ Storage (Port 8090)
Consumes product and order events from Kafka and persists them to a MySQL database using SQLAlchemy ORM. Exposes endpoints for querying events by timestamp range, enabling other services to fetch historical data.

## ðŸ“Š Processing (Port 8100)
Runs on a background scheduler to periodically aggregate statistics from the Storage service. Tracks running totals, highest prices, and peak quantities for both products and orders. Persists stats snapshots to SQLite.

## ðŸ” Audit (Port 8110)
Allows direct inspection of any event stored in Kafka by index and event type. Useful for debugging and verifying event integrity across the system.

## ðŸ“‹ Event Logger (Port 8120)
A cross-cutting monitoring service. All other services report lifecycle events (e.g. "connected to Kafka") to this service via a dedicated Kafka topic. Stores events by code in SQLite and exposes a stats endpoint grouped by event code.

## ðŸš¨ Anomaly Detector (Port 8130)
Consumes events from Kafka in real time and flags products or orders with prices outside of configured thresholds. Persists detected anomalies to SQLite with descriptions and trace IDs for traceability.

## ðŸ–¥ Dashboard UI
A frontend interface for visualizing statistics, event logs, and anomaly reports from the backend services.

# ðŸ”Ž Example API Endpoints

- **Create Product:** `POST /receiver/products`
- **Place Order:** `POST /receiver/orders`
- **Get Product Events:** `GET /storage/products?start_timestamp=...&end_timestamp=...`
- **Get Order Events:** `GET /storage/orders?start_timestamp=...&end_timestamp=...`
- **Get Stats:** `GET /processing/stats`
- **Get Audit Event:** `GET /audit/products/{index}`
- **Get Event Log Stats:** `GET /event-logger/stats`
- **Get Anomaly Stats:** `GET /anomaly-detector/anomalies?event_type=products`

# ðŸ³ Running the Application

1. Clone the repository.
2. Configure `app_conf.yaml` and `log_conf.yaml` for each service, or provide them via `/config/` for test environments.
3. Ensure Kafka and MySQL are running and accessible.
4. Run:

```
docker compose up -d --build
```

This will start all services along with the required databases.

# ðŸŽ¯ Future Improvements

- User authentication with JWT
- API documentation with Swagger UI
- Cloud deployment (AWS or GCP)
- Expanded anomaly detection rules beyond price thresholds
- Frontend analytics dashboard enhancements

# ðŸ“Œ Purpose

This project was built to demonstrate:

- Event-driven microservices architecture
- Asynchronous inter-service communication via Apache Kafka
- RESTful API design with OpenAPI/Connexion
- Multi-database persistence (MySQL + SQLite)
- Containerized deployment with Docker
- Real-time anomaly detection and system health monitoring