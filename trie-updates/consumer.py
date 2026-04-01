import os

from confluent_kafka import Consumer
import requests
config = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:45715'),
    'group.id': 'trie-updates-consumers',
    'auto.offset.reset': 'earliest'
}
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:8000')
ROUTER_URL = os.getenv('ROUTER_URL', 'http://localhost:8001')
consumer = Consumer(config)
consumer.subscribe(['trie-updates'])
import json
def consume_trie_updates():
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            print('Received message: {}'.format(msg.value().decode('utf-8')))
            payload = json.loads(msg.value().decode('utf-8'))
            print(f"User {payload['user_id']} updated trie with query '{payload['query']}' and freq {payload['freq']} at {payload['timestamp']}")
            response = requests.put(f"{ROUTER_URL}/tries/update_frequency", params={"query": payload['query'], "freq": payload['freq']})
            if response.status_code == 200:
                print(f"Successfully updated frequency for query '{payload['query']}'")
            else:
                    print(f"Failed to update frequency for query '{payload['query']}'. Server responded with status code {response.status_code} and message: {response.text}")
            print(f"Response from server: {response.json()}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        consumer.close()



if __name__ == "__main__":
    consume_trie_updates()