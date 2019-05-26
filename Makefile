BASH=bash -l -c
REMOTE=ssh -i ~/.ec2/secretkey.pem ubuntu@13.57.210.173
CCORE=jreportcore

build:
	docker-compose build

up:
	docker-compose up -d

run: up
	docker-compose exec $(CCORE) ./manage.py runserver 0.0.0.0:8000

clean:
	docker-compose stop && docker-compose rm -f

pull:
	git pull origin master

stop:
	docker-compose stop

start:
	docker-compose start

ps:
	docker-compose ps

restart: stop start ps

update: pull clean build

update_with_migrations: pull clean build up migrate restart ps

showlogs:
	docker-compose logs -f --tail 100

migrate:
	docker-compose exec $(CCORE) ./manage.py migrate

pipi:
	docker-compose exec $(CCORE) pip install -r requirements/dev.txt

celery:
	docker-compose exec $(CCORE) celery -A config worker -B -l info

celery_local:
	docker-compose exec $(CCORE) celery -A config worker -B -l info --config config.settings.local

createsuperuser:
	docker-compose exec $(CCORE) ./manage.py createsuperuser

bash:
	docker-compose exec $(CCORE) bash

CMD=
manage:
	docker-compose exec $(CCORE) ./manage.py $(CMD)

shell:
	docker-compose exec $(CCORE) ./manage.py shell

makemigrations:
	docker-compose exec $(CCORE) ./manage.py makemigrations

deploy:
	$(REMOTE) 'cd /home/ubuntu/backend/backend/ && git pull'
	$(REMOTE) 'sudo supervisorctl restart all'

remote_migrate:
	$(REMOTE) 'DJANGO_SETTINGS_MODULE="config.settings.stage" /home/ubuntu/backend/env/bin/python /home/ubuntu/backend/backend/manage.py migrate'

ssh:
	$(REMOTE)

DUMPNUM=190327
dumpdb:
	rm -f ./odindump_$(DUMPNUM).sql || true
	pg_dump -h omdb.curandsizatj.us-west-1.rds.amazonaws.com -U odinmoney -d om_general > odindump_$(DUMPNUM).sql
	psql -h 127.0.0.1 -p 35432 -U postgres -c "CREATE DATABASE odin_$(DUMPNUM);"
	psql -h 127.0.0.1 -p 35432 -U postgres odin_190327 < ./odindump_$(DUMPNUM).sql
