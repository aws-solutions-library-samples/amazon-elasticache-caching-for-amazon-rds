# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import random


def read_write(p):
    return 1 if random.triangular(0, 1, p) < p else 0


def run_read_query(engine, query):
    """
    Define a function to execute a SQL query using the current thread's connection
    """
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
        return result


def run_write_query(engine, query):
    """
    Define a function to execute a SQL insert query using the current thread's connection
    Note: we're not gracefully handling exceptions for example if a Unique contraint triggers a duplicate
    """
    with engine.connect() as conn:
        try:
            result = conn.execute(query)
            conn.commit()
            return result
        except:
            pass
