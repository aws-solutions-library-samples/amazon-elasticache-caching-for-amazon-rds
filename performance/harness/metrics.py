# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import random
import threading
import time
from tqdm import trange
from harness.queries import read_write, run_read_query, run_write_query
from harness.main import thead_metrics, cache_miss, cache_hit, num_keys, reads, writes


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
