# CI/CD Pipeline - Инструкции по деплою

## Настройка удаленного сервера

### 1. Создание и настройка сервера

- Создайте виртуальную машину Ubuntu 24.04 LTS
- Зафиксируйте публичный IP адрес

### 2. Установка системных зависимостей

Выполните на сервере:

sudo apt update
sudo apt upgrade -y
sudo apt install python3.12 python3.12-venv python3.12-dev -y
sudo apt install postgresql postgresql-contrib -y
sudo apt install redis-server -y
sudo apt install nginx -y

### 3. Настройка базы данных PostgreSQL

Выполните:

sudo -u postgres psql

В psql выполните:

CREATE DATABASE lms_db;
CREATE USER lms_user WITH PASSWORD 'ваш_надежный_пароль';
GRANT ALL PRIVILEGES ON DATABASE lms_db TO lms_user;
ALTER DATABASE lms_db OWNER TO lms_user;
\q

### 4. Настройка брандмауэра

sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw enable

### 5. Настройка SSH доступа

- Создайте SSH ключи на локальной машине
- Добавьте публичный ключ в ~/.ssh/authorized_keys на сервере
- Протестируйте подключение

## GitHub Actions Workflow

### Настройка Secrets в GitHub

В репозитории GitHub перейдите:
Settings → Secrets and variables → Actions

Добавьте следующие secrets:

1. SSH_PRIVATE_KEY - приватный SSH ключ для доступа к серверу
2. SERVER_HOST - IP адрес вашего сервера (например: 158.160.136.193)
3. SERVER_USER - имя пользователя на сервере (например: voyager)
4. DEPLOY_PATH - путь на сервере (например: /home/voyager/djangoproject_hw_2)

### Автоматический деплой

При каждом пуше в ветки main, master или develop:

1. GitHub Actions запускает автоматические тесты
2. Если тесты проходят успешно, происходит автоматический деплой
3. Файлы копируются на сервер через SCP
4. Выполняется скрипт деплоя `deploy_server.sh`
5. Сервисы перезапускаются через systemd

## Ручной деплой

### Скопируйте проект на сервер:

scp -r . пользователь@ip_адрес_сервера:/путь/на/сервере

### Выполните деплой:

cd /путь/на/сервере
chmod +x deploy_server.sh
./deploy_server.sh

## Systemd службы

### Gunicorn (веб-сервер)

Служба: /etc/systemd/system/gunicorn.service

Команды управления:

sudo systemctl status gunicorn.service
sudo systemctl restart gunicorn.service
sudo systemctl stop gunicorn.service

### Celery (фоновые задачи)

Службы: celery.service и celerybeat.service

Команды управления:

sudo systemctl status celery.service
sudo systemctl restart celery.service

## Мониторинг

### Просмотр логов

Логи Gunicorn:
sudo journalctl -u gunicorn.service -f

Логи Celery:
sudo journalctl -u celery.service -f

Логи PostgreSQL:
sudo tail -f /var/log/postgresql/postgresql-16-main.log

### Проверка доступности

Внутренний доступ:
curl http://localhost:8000/api/docs/

Внешний доступ:
curl http://ваш_ip:8000/api/docs/

## Устранение неполадок

### Порт 8000 занят

sudo lsof -i :8000
sudo kill -9 PID_процесса

### Ошибки базы данных

sudo systemctl restart postgresql
cd /путь/к/проекту && python manage.py migrate

### Ошибки Redis

sudo systemctl restart redis-server