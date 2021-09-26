import pika

import backend.settings as settings
from backend.celery import app
from celery.utils.log import get_task_logger


@app.task
def receive_messages():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(settings.RABBITMQ_HOST, settings.RABBITMQ_PORT)
    )
    channel = connection.channel()
    queue_name = settings.RABBITMQ_QUEUE_NAMES['bot2backend']
    channel.queue_declare(queue=queue_name)
    # Just for now we don't need to proceed messages from bot
    channel.basic_consume(queue=queue_name, on_message_callback=lambda: None, auto_ack=True)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()


@app.task
def send_message(message_id):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(settings.RABBITMQ_HOST, settings.RABBITMQ_PORT)
    )
    channel = connection.channel()
    queue_name = settings.RABBITMQ_QUEUE_NAMES['backend2bot']
    channel.queue_declare(queue=queue_name)
    channel.confirm_delivery()
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=str(message_id),
                          properties=pika.BasicProperties(content_type='text/plain',
                                                          delivery_mode=1)
                          )
    connection.close()
