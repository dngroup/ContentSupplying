from celery import Celery


from src import encoding


# New celery worker connected to default RabbitMQ
app = Celery('worker')
app.config_from_object('celeryconfig')


@app.task
def msEncoding(title,settings_url,download_url,callback):
    encoding.msEncoding(title,settings_url,download_url,callback)