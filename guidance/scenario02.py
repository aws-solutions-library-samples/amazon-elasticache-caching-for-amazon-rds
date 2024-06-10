# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import random
import threading
import sys
import os
import time
import string
import argparse
from redis import RedisCluster as Redis
# from redis import Redis as Redis
from sqlalchemy import create_engine, text
from decouple import config

read = 0
write = 0
engine = None
booking_id = 0
cache_hit = 0
cache_miss = 0

# Set the connection parameters

parser = argparse.ArgumentParser(description=f"AWS Samples - Harness test for RDBMS and Cache")
parser.add_argument('--users', type=int, default=4, help='Number of users to simulate.')
parser.add_argument('--queries', type=int, default=10, help='Number of queries to be run by each thread.')
parser.add_argument('--read_rate', type=int, default=80, help='Number of queries to be run by each thread.')
parser.add_argument('--ssl', type=lambda x: (str(x).lower() == 'true'), default=False, help='True/False Enable/Disable ElastiCache TLS default is False')
parser.add_argument('--log_tag', type=str, help='A unique string to be applied to the logfile.')

args = parser.parse_args()

# Adjust read rate to between 0 and 1
args.read_rate = args.read_rate/100
# If no log tag passed in generate one
if not args.log_tag:
    args.log_tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


DB_ENGINE=f"mysql+pymysql"
params = {
    "host": config('MYSQL_HOST', "localhost"),
    "database": config('MYSQL_DB', "db_name"),
    "user": config('MYSQL_USER', "admin"),
    "password": config('MYSQL_PASS', "secret_password"),
    "port": config('MYSQL_PORT', 3306),
    "ec_redis_host": config('EC_REDIS_HOST', 'localhost'),
    "ec_redis_port": config('EC_REDIS_PORT', 6379),
  }

SQLALCHEMY_DATABASE_RW_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
SQLALCHEMY_DATABASE_RO_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"

READ_QUERY = text("select p.firstname, p.lastname, count(*) \
                from airportdb_small.passenger p, airportdb_small.booking b \
                where p.passenger_id = :passenger \
                and p.passenger_id = b.passenger_id \
                group by p.firstname, p.lastname")

WRITE_QUERY = text("INSERT into airportdb_small.booking (flight_id, passenger_id, price, seat) \
                    VALUES(:flight, :passenger, 1000.00, '1A')")


# Define a thread-local storage object to hold connections
thread_local = threading.local()

# Test if we can create an engine
try:
  engine_rw = create_engine(SQLALCHEMY_DATABASE_RW_URL, pool_size=args.users, max_overflow=50)
  engine_rw.connect()

  engine_ro = create_engine(SQLALCHEMY_DATABASE_RO_URL, pool_size=args.users, max_overflow=50)
  engine_ro.connect()

  print("Connected to Database")

  redis_write = Redis(host=params['ec_redis_host'], port=params['ec_redis_port'], ssl=args.ssl, decode_responses=False, socket_connect_timeout = 5)
  redis_read  = Redis(host=params['ec_redis_host'], port=params['ec_redis_port'], ssl=args.ssl, decode_responses=False, socket_connect_timeout = 5, read_from_replicas=True)
  # To force all connections to the primary
  # redis_read = redis_write
  print("Connected to ElastiCache")

except Exception as e:
  print("SQLAlchemy create engine connection or ElastiCache exception occurred")
  print(e)
  exit(1)


# Random read write query selector
def read_write(p):
    return 1 if random.triangular(0, 1, p) < p else 0


# Run a read query
def run_read_query(engine, query):
    """
    Define a function to execute a SQL query using the current thread's connection
    """
    with engine.connect() as conn:
         result = conn.execute(query).fetchall()
    return result


# Run a write query
def run_write_query(engine, query):
    """
    Define a function to execute a SQL insert query using the current thread's connection
    """
    with engine.connect() as conn:
         result = conn.execute(query)
         # conn.commit()
    return result


def metrics_by_time():
    """
    Define a function to run in a thread
    """
    global READ_QUERY, WRITE_QUERY, read_rate, read, write, cache_hit, cache_miss

    for q in range(args.queries):
        
        passenger_id = random.randrange(4,35000)
        flight_id = random.randrange(4,35000)
        # the limited data set and FK restrictions require a valid fligth ID 
        # flight_id =  run_read_query(engine_ro, text("select flight_id from flight order by rand() limit 1"))[0][0]
        key = f"bookings:{passenger_id}"
        
        if read_write(args.read_rate):
           start_time = time.time()
           data = redis_read.get(key)
           end_time = time.time()
           read += 1
           if data:
              cache_hit += 1
           else:
              read_query = READ_QUERY.bindparams(passenger=passenger_id)
              data = run_read_query(engine_ro, read_query)
              end_time = time.time()
              redis_write.set(key, str(data))
              # redis_write.setex(key, 3600, str(data))
              cache_miss += 1 
        else:
           start_time = time.time()
           write_query = WRITE_QUERY.bindparams(flight=flight_id, passenger=passenger_id)
           run_write_query(engine_rw, write_query)
           end_time = time.time()
           # Update the cache after write
           read_query = READ_QUERY.bindparams(passenger=passenger_id)
           data = run_read_query(engine_ro, read_query)
           redis_write.set(key, str(data))
           # different options to update the cache with a TTL or to delete
           # redis_write.setex(key, 3600, str(data))
           # redis_write.delete(key)
           write += 1

        query_time = end_time - start_time
        timestamp = str(int(start_time))

        if timestamp not in thread_metrics:
            thread_metrics[timestamp] = {
                "count": 1,
                "query_time": query_time,
                "min_time": query_time,
                "max_time": query_time,
             }
        else:
            thread_metrics[timestamp]["count"] += 1
            thread_metrics[timestamp]["query_time"] += query_time
            if query_time < thread_metrics[timestamp]["min_time"]:
                thread_metrics[timestamp]["min_time"] = query_time
            if query_time > thread_metrics[timestamp]["max_time"]:
                thread_metrics[timestamp]["max_time"] = query_time
    
       
threads = list()
thread_metrics = dict()

for i in range(args.users):
    # Create and start a thread
    thread = threading.Thread(target=metrics_by_time)
    threads.append(thread)
    thread.start()

for i, thread in enumerate(threads):
    # Wait for the thread to finish
    thread.join()

print("Reads: " + str(read))
print("Writes: " + str(write))
print("Cache hits: " + str(cache_hit))
print("Cache misses: " + str(cache_miss))

# Write out the captured statistics to a log file
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/scenario02_{os.getpid()}_{args.log_tag}.json"

with open(log_file, "w") as f:
    f.write(json.dumps(thread_metrics, indent=2))

print("Logfile located here: " + log_file)
