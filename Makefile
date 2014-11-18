.PHONY: run clean install deploy

PYTHON=python3
export PATH:=.env/bin:$(PATH)

run: .env
	python manage.py runserver 0.0.0.0:8000

clean:
	find . -iname "*.pyc" -delete
	find . -iname "*.pyo" -delete
	find . -iname "__pycache__" -delete

deploy: .env
	python manage.py migrate
	python manage.py loaddata choices
	python manage.py collectstatic --noinput
	touch aol/wsgi.py

install: .env
	mysql -e "CREATE DATABASE IF NOT EXISTS aol"
	python manage.py migrate
	python manage.py loaddata choices

.env:
	$(PYTHON) -m venv .env
	curl https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py | python
	pip install -r requirements.txt
