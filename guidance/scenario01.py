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
from sqlalchemy import create_engine, text
from decouple import config

read = 0
write = 0
engine = None

# Get the workload parameters 
parser = argparse.ArgumentParser(description=f"AWS Samples - Harness test for RDBMS and Cache")
parser.add_argument('--users', type=int, default=4, help='Number of users to smulate.')
parser.add_argument('--queries', type=int, default=10, help='Number of queries to be run by each thread.')
parser.add_argument('--read_rate', type=int, default=80, help='Number of queries to be run by each thread.')
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
  }

SQLALCHEMY_DATABASE_RW_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
SQLALCHEMY_DATABASE_RO_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"

READ_QUERY = text("SELECT p.firstname, p.lastname, COUNT(*) \
                FROM airportdb.passenger p, airportdb.booking b \
                WHERE p.passenger_id = :passenger \
                AND p.passenger_id = b.passenger_id \
                GROUP BY p.firstname, p.lastname")

WRITE_QUERY = text("INSERT into airportdb.booking (flight_id, passenger_id, price, seat) \
                    VALUES(:flight, :passenger, 1000.00, '1A')")


# Define a thread-local storage object to hold connections
thread_local = threading.local()

# Test if we can create an engine
try:
  engine_rw = create_engine(SQLALCHEMY_DATABASE_RW_URL, pool_size=args.users, max_overflow=10)
  engine_rw.connect()

  engine_ro = create_engine(SQLALCHEMY_DATABASE_RO_URL, pool_size=args.users, max_overflow=10)
  engine_ro.connect()

except Exception as e:
  print("SQLAlchemy create engine connection exception. Make sure the env. parameters are set.")
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
    global READ_QUERY, WRITE_QUERY, read_rate, read, write

    for q in range(args.queries):
        
        passenger_id = random.randrange(4,35000)
        flight_id = random.randrange(4,35000)
        # the limited data set and FK restrictions require a valid fligth ID 
        # flight_id =  run_read_query(engine_ro, text("select flight_id from flight order by rand() limit 1"))[0][0]
        
        if read_write(args.read_rate):
           start_time = time.time()
           read_query = READ_QUERY.bindparams(passenger=passenger_id)
           data = run_read_query(engine_ro, read_query)
           end_time = time.time()
           read += 1 
        else:
           start_time = time.time()
           write_query = WRITE_QUERY.bindparams(flight=flight_id, passenger=passenger_id)
           run_write_query(engine_rw, write_query)
           end_time = time.time()
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

# Write out the captured statistics to a log file 
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/scenario01_{os.getpid()}_{args.log_tag}.json"

with open(log_file, "w") as f:
    f.write(json.dumps(thread_metrics, indent=2))

print("Logfile located here: " + log_file)
