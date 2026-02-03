.PHONY: up down build logs restart clean shell test migrate createsuperuser

up:
docker-compose up -d

down:
docker-compose down

rebuild:
docker-compose down
docker-compose build --no-cache
docker-compose up -d

logs:
docker-compose logs -f

logs-web:
docker-compose logs -f web

logs-celery:
docker-compose logs -f celery_worker

logs-beat:
docker-compose logs -f celery_beat

restart:
docker-compose restart $(service)

clean:
docker-compose down -v
docker system prune -f

shell:
docker-compose exec web python manage.py shell

test:
docker-compose exec web python manage.py test

makemigrations:
docker-compose exec web python manage.py makemigrations

migrate:
docker-compose exec web python manage.py migrate

createsuperuser:
docker-compose exec web python manage.py createsuperuser

status:
docker-compose ps

collectstatic:
docker-compose exec web python manage.py collectstatic --noinput

loaddata:
docker-compose exec web python manage.py loaddata groups.json

healthcheck:
curl -f http://localhost:8000/api/docs/ || echo "API недоступен"
