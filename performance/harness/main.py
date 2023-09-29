# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import random
import string
import sys
import threading
import time
from tqdm import trange
from rich import print
from harness.databases import create_connections
from harness.graphs import create_charts
from harness.queries import read_write, run_read_query, run_write_query

# cache hit miss counters
reads = 0
writes = 0
cache_hit = 0
cache_miss = 0
engine = None
num_keys = set()
thread_metrics = dict()


def show_results(db_type: str, log_ext: str) -> str:
    timestamps = list(thread_metrics.keys())
    print(f"First second stats {thread_metrics[timestamps[0]]}")
    print(f"Last second stats {thread_metrics[timestamps[-1]]}")
    print(f"Total Reads:\t{reads:,}")
    print(f"Cache Hits:\t{cache_hit:,}")
    print(f"Cache Miss:\t{cache_miss:,}")
    print(f"Writes:\t{writes:,}")
    print(f"Keys:\t{len(num_keys)}")
    # file_name = f"logs/rdbms/harness_{db_type}_{os.getpid()}_{int(time.time())}.json"
    file_name = f"logs/rdbms/harness_{db_type}_{os.getpid()}_{log_ext}.json"
    with open(file_name, "w") as f:
        f.write(json.dumps(thread_metrics, indent=2))
    print(f"Logfile located here: {file_name}")
    return file_name


def test(max_queries: int):
    for i in trange(max_queries):
        time.sleep(random.random())


def metrics_by_time(engine, engine_rw, engine_ro, redis_write, redis_read, WRITE_QUERY, READ_QUERY, max_queries, read_rate):
    """
    Lazy Loading or Cache Aside Function to run {max_queries} and use a percentage of {read_rate} to split read/writes from the database.
    """
    global thread_metrics, cache_miss, num_keys, reads, writes, cache_hit
    thread_name = f"tid-{threading.current_thread().native_id}"
    redis_write.ping()
    for q in trange(max_queries):
        # Simple query with no join statement
        # booking_id = random.randrange(1,5000000)
        # query = f"select flight_id, passenger_id, price, stuff from booking where booking_id = " + str(booking_id)
        # Medium query with 1 join statement
        passenger_id = random.randrange(4,35000)
        flight_id = random.randrange(4,35000)
        #key = "bookings:" + str(hashlib.sha256(query.encode()).hexdigest())        
        key = f"bookings:{passenger_id}"      
        # Lazy loading approach
        # but, for better simulation only use the cache 80% of the time
        # i.e. simulate that the buffer gets invalidated and only p /% time is valid
        # 1) Try the cache
        if read_write(read_rate):
           start_time = time.time()
           data = redis_read.get(key)
           end_time = time.time()
           reads += 1
           if data:
               cache_hit += 1
           else:
              read_query = READ_QUERY.bindparams(passenger=passenger_id)
              data = run_read_query(engine_ro, read_query)
              redis_write.set(key, str(data))
              end_time = time.time()
              cache_miss += 1
        else:
          start_time = time.time()
          write_query = WRITE_QUERY.bindparams(flight=flight_id, passenger=passenger_id)
          run_write_query(engine_rw, write_query)
          end_time = time.time()
          read_query = READ_QUERY.bindparams(passenger=passenger_id)
          data = run_read_query(engine, read_query)
          redis_write.set(key, str(data))
          writes += 1
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



def run_harness_test(db_type: str, max_threads: int, max_queries: int, read_rate: float):
    global thread_metrics
    [rdbms_engine, rdbms_rw, rdbms_ro, cache_rw, cache_ro, WRITE_QUERY, READ_QUERY] = create_connections(db_type=db_type, max_threads=max_threads)
    threads = list()
    # thread_metrics = dict()
    print(f"Spawning {max_threads} new threads")
    for i in trange(max_threads):
        # Create and start a thread
        thread = threading.Thread(target=metrics_by_time, args=(rdbms_engine, rdbms_rw, rdbms_ro, cache_rw, cache_ro, WRITE_QUERY, READ_QUERY, max_queries, read_rate,))
        # thread = threading.Thread(target=test, args=(max_queries,))
        threads.append(thread)
        thread.start()
    for i, thread in enumerate(threads):
        # Wait for the thread to finish
        thread.join()
    # return thread_metrics


def main(db_type: str, max_threads: int, max_queries: int, read_rate: int):
    # Define a thread-local storage object to hold connections
    thread_local = threading.local()
    read_rate = read_rate / 100
    log_ext = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    print(f"RDBMS Engine:\t{db_type}")
    print(f"Number of threads:\t{max_threads}")
    print(f"Number of queries:\t{max_queries:,}")
    print(f"Read %:\t{read_rate}")
    print(f"log_ext:\t{log_ext}")
    run_harness_test(db_type=db_type, max_threads=max_threads, max_queries=max_queries, read_rate=read_rate)
    file_name = show_results(db_type=db_type, log_ext=log_ext)
    create_charts(rdbms=db_type, read_rate=read_rate, file_name=file_name, log_ext=log_ext)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=f"AWS Samples - Harness test for RDBMS and Cache")
    parser.add_argument('--rdbms', type=str, default='MYSQL', help='RDBMS Engine.')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads to spawn.')
    parser.add_argument('--queries', type=int, default=10, help='Number of queries to be run by each thread.')
    parser.add_argument('--read_rate', type=int, default=80, help='Number of queries to be run by each thread.')
    args = parser.parse_args()
    main(args.rdbms, args.threads, args.queries, args.read_rate)
