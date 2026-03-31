import os

from confluent_kafka import Producer
print("KAFKA HOST:", os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'NOT FOUND'))
config = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:45715'),
}

producer =  Producer(config)
def delivery_callback(err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

import time
import json
def log_search_event(query : str):
    topic = "search-events"
    user_id = 1
    payload = {
        "user_id": user_id,
        "query": query,
        "timestamp": int(time.time())
    }
    payload_ser = json.dumps(payload).encode('utf-8')
    producer.produce(topic=topic, value=payload_ser, callback=delivery_callback, key=str(user_id))
    producer.poll(0)
    producer.flush()
    # The `producer.poll(0)` method is used to trigger the delivery of any messages that are currently in the producer's buffer, while the `producer.flush()` method is used to block until all messages in the producer's buffer have been delivered to the Kafka broker


