from locust import HttpUser, task, between
import random

prefixes = [
    "app", "appl", "apple",
    "goo", "goog", "googl",
    "the", "ther", "there",
    "mic", "micr", "micro",
    "ban", "bana", "banan",
    "new", "news",
    "hel", "hell", "hello",
    "wor", "worl", "world",
    "cat", "cats",
    "dog", "dogs",
    "sun", "sund",
    "sky", "skyl",
    "ran", "rand", "rando",
]

words = [
    "apple", "google", "there", "microsoft",
    "banana", "news", "hello", "world",
    "cat", "dog", "sun", "sky", "random",
    "application", "thunder", "nature",
    "network", "system", "cloud", "data"
]

class AutocompleteUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def autocomplete(self):
        prefix = random.choice(prefixes)
        self.client.get("/autocomplete", params={"prefix": prefix})

    @task(1)
    def search(self):
        word = random.choice(words)
        self.client.get("/tries/search", params={"word": word})