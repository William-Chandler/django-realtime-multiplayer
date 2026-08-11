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
  
- Dedicated accounts app with automatic UserProfile creation

- Clean separation between Django HTTP views and Channels WebSocket consumers

# Stack Overview

Django:	Core web framework

Django Channels:	WebSocket and asynchronous support

Daphne:	ASGI server

Redis:	Channel layer and pub/sub system

Docker Compose:	Container orchestration

Python 3:	Application runtime


# Project Structure
```
project-root/
│
├── app/                         # Django project root
│   ├── mysite/                  # Django settings, ASGI, URLs
│   ├── accounts/                # Django app (models, signals, migrations, templates)
│   ├── rooms/               	  # Django app (models, signals, migrations, templates)
│   ├── core/                    # Channels routing + consumers (not a Django app)
│   ├── manage.py
│
├── templates/                   # Global HTML templates
│   └── core/
│       └── index.html
│
├── static/                      # Global static assets (JS, CSS)
│   └── core/
│       ├── game.js
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── redis.conf
├── requirements.txt
├── entrypoint.sh				  # Configures development or production server depending on .env variable   
├── .env                         # Environment variables (ignored by Git)
├── .gitignore
└── README.md
```
## Notes on Architecture
- ```accounts``` is a full Django app containing models, migrations, signals, user logic, and templates.

- Likewise, ```rooms``` is a full Django app with its own models, migrations, etc.

- ```UserProfile``` stores per‑user preferences (currently colour).

- ```core``` is not a Django app; it contains Channels routing and WebSocket consumers only.

- Redis stores:

	- latest player positions (```HSET position```)

	- realtime movement events (```XADD game-stream```)
	
	- Note: all Redis function calls are wrapped to stop them from crashing the system in dev. Should operate as is in production by activating Redis in settings.py.

- Templates and static files are stored in global directories (```templates/``` and ```static/```).

- The game client (```game.js```) receives colour information from the server and renders each player accordingly.

- This separation keeps HTTP and WebSocket layers clean and maintainable.

# Environment Variables

Create a .env file in the project root:
```
DJANGO_SECRET_KEY=your-secret-key
POSTGRES_DB=your-db
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432
DJANGO_ENV=development
```
The .env file is excluded from version control via .gitignore.

# Running the Project with Docker

## Build and start all services
```
docker compose up --build
```
## Stop all services
```
docker compose down
```
## Run Django management commands inside the container
```
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```
# Realtime Architecture

Django Channels communicates through Redis using the following flow:
```
WebSocket Client → Daphne → Channels → Redis → Consumers
```
This architecture supports:

- Multiplayer game state updates

- Chat systems

- Collaborative tools

- Live dashboards

- Any realtime interaction pattern

# Development Workflow

## Code changes

Django reloads automatically inside Docker when in development environment. Production requires full rebuild to apply changes to code. 

## Add new dependencies

Update requirements.txt and rebuild:
```
docker compose up --build
```
## Run tests
```
docker compose exec web pytest
```
# Deployment Notes

This project can be deployed to:

- Docker Swarm

- Kubernetes

- Render

- Railway

- DigitalOcean Apps

- AWS ECS

For production:

- Set DJANGO_ENV=production in .env

- Set DJANGO_DEBUG=False in settings.py

- Configure DJANGO_ALLOWED_HOSTS

- Use a persistent Redis instance

- Serve static files via Nginx or a CDN
