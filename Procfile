release: python manage.py migrate
web: daphne mainproject.asgi:application --port $PORT --bind 0.0.0.0
worker: python manage.py runworker channel_layer
