# Django Realtime Multiplayer

A fully containerised Django Channels starter kit for building realtime multiplayer applications.
This project uses Django, Channels, Daphne, Redis, and Docker to provide a robust foundation for realtime communication over WebSockets.

# Features

- Realtime communication using Django Channels

- WebSocket support via Daphne ASGI server

- Redis channel layer backend ready to be enabled upon deployment to cloud/Linux server

- Dockerised development environment

- Environment‑based configuration using .env

- Production‑ready project structure

- Automatic static file collection

- Hot‑reload development workflow

# Stack Overview

Django:	Core web framework

Django Channels:	WebSocket and asynchronous support

Daphne:	ASGI server

Redis:	Channel layer and pub/sub system

Docker Compose:	Container orchestration

Python 3:	Application runtime


# Project Structure

project-root/

│

├── app/                     # Django project

│   ├── mysite/                 # Django settings, ASGI, URLs

│   ├── core/                # Main app (views, routing, consumers)

│   ├── manage.py

│

├── docker-compose.yml

├── Dockerfile

├── requirements.txt

├── .env                     # Environment variables (ignored by Git)

├── .gitignore

└── README.md

# Environment Variables

Create a .env file in the project root:

DJANGO_SECRET_KEY=your-secret-key

DJANGO_DEBUG=True

DJANGO_ALLOWED_HOSTS=*

REDIS_HOST=redis

REDIS_PORT=6379

The .env file is excluded from version control via .gitignore.

# Running the Project with Docker

## Build and start all services

docker compose up --build

## Stop all services

docker compose down

## Run Django management commands inside the container

docker compose exec web python manage.py migrate

docker compose exec web python manage.py createsuperuser

# Realtime Architecture

Django Channels communicates through Redis using the following flow:

WebSocket Client → Daphne → Channels → Redis → Consumers

This architecture supports:

- Multiplayer game state updates

- Chat systems

- Collaborative tools

- Live dashboards

- Any realtime interaction pattern

# Development Workflow

## Code changes

Django reloads automatically inside Docker.

## Add new dependencies

Update requirements.txt and rebuild:

docker compose up --build

## Run tests

docker compose exec web pytest

# Deployment Notes

This project can be deployed to:

- Docker Swarm

- Kubernetes

- Render

- Railway

- DigitalOcean Apps

- AWS ECS

For production:

- Set DJANGO_DEBUG=False

- Configure DJANGO_ALLOWED_HOSTS

- Use a persistent Redis instance

- Serve static files via Nginx or a CDN
