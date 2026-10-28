# Stock Prediction Platform - Docker Deployment Guide

This guide details how to spin up the entire Full-Stack Stock Prediction SaaS locally using Docker Desktop.

## Prerequisites
* Ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Verify port `3000` (Frontend), `8000` (Backend API), and `5432` (PostgreSQL) are completely free on your local machine.

## Quickstart

1. **Verify `.env` parameters:**
   Check the root `.env` file and ensure the `JWT_SECRET_KEY` is secure if deploying beyond local development. The database credentials `DB_USER` and `DB_PASSWORD` are automatically forwarded into the PostgreSQL container.

2. **Trigger the orchestrator:**
   Open your terminal in the root directory where `docker-compose.yml` resides and execute:
   ```bash
   docker-compose up --build -d
   ```
   *(Note: The `-d` flag runs the massive cluster silently in the background so it doesn't lock up your terminal. Drop the flag if you want to watch the logs natively).*

3. **Validate the Deployment:**
   * Wait roughly ~45 seconds for the `PostgreSQL` health checks to pass and the `FastAPI` ASGI server to boot successfully on Python 3.8.0.
   * Open your browser and navigate to: **[http://localhost:3000](http://localhost:3000)**

## Architecture Topology
When ran, Docker provisions an isolated virtual bridge network between 3 unique Linux (Alpine/Slim) nodes:
* `stock_db`: An isolated PostgreSQL 15 database persisting data onto your local hard drive via tracked volumes.
* `stock_backend`: A Python 3.8.0 microservice running Uvicorn + FastAPI, communicating internally with `stock_db` and sharing the `backend_api/ml/models/` volume directory to serialize training artifacts.
* `stock_frontend`: Node 18 Server shipping the compiled, optimized Next.js App Router UI.

## Troubleshooting

* **Viewing Backend Error Logs:** 
  If predictions are failing or the database fails to bind: `docker logs stock_backend -f`
* **Shutting Down the Stack:** 
  When finished: `docker-compose down` (Add `-v` to permanently delete the Database tables).
