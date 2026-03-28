from confluent_kafka import Consumer
from producer import log_update_trie_event

config={
    'bootstrap.servers': 'localhost:45715',
    'group.id': 'search-event-consumers',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(config)
consumer.subscribe(['search-events'])
query_counter = {} # this is a simple in-memory counter to keep track of the number of times each query has been searched, it will be used to update the trie
def reset_query_counter():
    global query_counter
    for query, freq in query_counter.items():
        print(f"Updating trie with query '{query}' and freq {freq}")
        log_update_trie_event(query, freq)
    query_counter = {}
import time
import json
original_time = time.time()
def consume_search_events():
    try:
        while True:
            curr_time = time.time()
            msg = consumer.poll(1.0)
            global original_time
            if curr_time - original_time >= 30:
                reset_query_counter()
                original_time = curr_time
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            print('Received message: {}'.format(msg.value().decode('utf-8')))
            payload = json.loads(msg.value().decode('utf-8'))
            print(f"User {payload['user_id']} searched for '{payload['query']}' at {payload['timestamp']}")
            query_counter[payload['query']] = query_counter.get(payload['query'], 0) + 1
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_search_events()