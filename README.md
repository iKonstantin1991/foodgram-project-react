![Actions Status](https://github.com/iKonstantin1991/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

Документация: http://localhost/api/docs/redoc


# Foodgram. Сервис для публикации рецептов.
## Описание
Проект Foodgram собирает рецепты пользователей. Каждому рецепту можно присвоить определеные тэги, добавлять их в избранное и в список покупок а затем скачивать этот список. Можно подписываться на интересных авторов.
## Стек
Python 3.8, Django 3.0.5, Django REST Framework, PostgreSQL, Docker, git
## Команды для запуска приложения
Перед запуском приложения убедитесь что у вас установлен docker, docker-compose
Для запуска приложения нужно:
- в дирректории backend/ приложения создать файл .env и прописать внутри него:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<your_django_secret_key>
```
что бы сгенерировать SECRET_KEY нужно из дирректории backend/ выполнить:
```python manage.py shell```

Затем:
```
from django.core.management.utils import get_random_secret_key  
get_random_secret_key()
```
Затем скопировать полученный ключ в .env

- В infra/nginx.conf изменить строку 3 на: 
```server_name <your_ip>;```

из дирректории infra/ выполнить команды
- ```docker-compose up -d```
- ```docker-compose exec backend python manage.py migrate --noinput```
- ```docker-compose exec backend python manage.py collectstatic --no-input```


## Команды для содания суперпользователя
Для создание суперпользователя выполните команду из дирректории infra/:<br>
```docker-compose exec backend python manage.py createsuperuser```<br>

## Заполнение базы начальными данными
Для заполнения базы начальными данными выполните команды из дирректории backend/.<br>
- ```docker-compose exec backend python manage.py loaddata init_data.json```

## Основные возможности
- Регистрация и вход по email и паролю
- Просмотр списка всех рецептов с фильрацией по тегам
### Для авторизированных пользователей
- Создание и редактирование рецептов
- Просмотр рецептов определенного автора
- Подписка(отписка) на интересных авторов
- Добавление(удаление) рецептов в избранное и в список покупок
- Возможность скачать список ингредиентов входящих в рецепты из списка покупок

## Контакты
Email: ikonstantin1991@mail.ru<br>
Telegram: @ikonstantin91
