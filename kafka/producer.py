from confluent_kafka import Producer

config = {
    'bootstrap.servers': 'localhost:45715',
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
def log_update_trie_event(query : str, freq : int):
    topic = "trie-updates"
    user_id = 1
    payload = {
        "user_id": user_id,
        "query": query,
        "freq": freq,
        "timestamp": int(time.time())
    }
    payload_ser = json.dumps(payload).encode('utf-8')
    producer.produce(topic=topic, value=payload_ser, callback=delivery_callback, key=str(user_id))
    producer.poll(0)
    producer.flush()