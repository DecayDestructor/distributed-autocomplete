#!/bin/bash
a=$1
ck() {
  if [ ! -d "env" ]; then
    echo "mk env"
    python3 -m venv env
    echo "ins req"
    env/bin/pip install -r requirements.txt httpx locust pytest
  fi
}
if [ "$a" = "env" ]; then
  ck
elif [ "$a" = "up" ]; then
  ck
  echo "up stk"
  docker compose up -d --build
elif [ "$a" = "dwn" ]; then
  echo "dwn stk"
  docker compose down
elif [ "$a" = "rst" ]; then
  echo "rst stk vols env img"
  docker compose down -v --rmi all --remove-orphans
  rm -rf env
  ck
  docker compose up -d --build
elif [ "$a" = "hyd" ]; then
  ck
  echo "run hyd"
  env/bin/python hydrate.py
elif [ "$a" = "kil" ]; then
  echo "kil s1"
  docker compose stop shard1
elif [ "$a" = "rev" ]; then
  echo "rev s1"
  docker compose start shard1
elif [ "$a" = "ldt" ]; then
  ck
  echo "run ldt"
  env/bin/locust -f locust/locustfile.py --host=http://localhost:8080
elif [ "$a" = "log" ]; then
  echo "tl lgs"
  docker compose logs -f
elif [ "$a" = "lgr" ]; then
  echo "tl rt lgs"
  docker compose logs -f router router2
elif [ "$a" = "tst" ]; then
  ck
  echo "run tst"
  env/bin/pytest server/tests/test_tries.py -v
else
  echo "err arg: env up dwn rst hyd kil rev ldt log lgr tst"
fi
