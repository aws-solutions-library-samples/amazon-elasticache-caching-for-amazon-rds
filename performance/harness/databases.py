# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from dotenv import load_dotenv
# from redis import Redis
from redis import RedisCluster as Redis
from sqlalchemy import create_engine, text
load_dotenv()


# RELATIONAL DATABASE MANAGEMENT SYSTEMS
def create_connections(db_type: str, max_threads: int) -> list:
    if db_type == 'MYSQL':
        DB_ENGINE=f"mysql+pymysql"
        params = {
            "host": os.environ.get('MYSQL_HOST', "localhost"),
            "database": os.environ.get('MYSQL_DB', "db_name"),
            "user": os.environ.get('MYSQL_USER', "admin"),
            "password": os.environ.get('MYSQL_PASS', "secret_password"),
            "port": os.environ.get('MYSQL_PORT', 3306),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        SQLALCHEMY_DATABASE_RW_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        SQLALCHEMY_DATABASE_RO_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        READ_QUERY = text("SELECT p.firstname, p.lastname, COUNT(b.booking_id) \
                        FROM airportdb.passenger p, airportdb.booking b \
                        WHERE p.passenger_id = :passenger \
                        AND p.passenger_id = b.passenger_id \
                        GROUP BY p.firstname, p.lastname")
        WRITE_QUERY = text("INSERT INTO airportdb.booking (flight_id, passenger_id, price, seat) \
                            VALUES (:flight, :passenger, 1000.00, '1A')")
    elif db_type == 'MARIADB':
        DB_ENGINE=f"mysql+pymysql"
        params = {
            "host": os.environ.get('MARIA_HOST', "localhost"),
            "database": os.environ.get('MARIA_DB', "db_name"),
            "user": os.environ.get('MARIA_USER', "admin"),
            "password": os.environ.get('MARIA_PASS', "secret_password"),
            "port": os.environ.get('MARIA_PORT', 3306),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    elif db_type == 'MSSQL':
        DB_ENGINE=f"mssql+pyodbc"
        params = {
            "host": os.environ.get('MSSQL_HOST', "localhost"),
            "database": os.environ.get('MSSQL_DB', "db_name"),
            "user": os.environ.get('MSSQL_USER', "Admin"),
            "password": os.environ.get('MSSQL_PASS', "secret_password"),
            "port": os.environ.get('MSSQL_PORT', 1433),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc:///?odbc_connect=DRIVER={{ODBC Driver 18 for SQL Server}};\
                SERVER={params['host']};Database={params['database']};\
                UID={params['user']};PWD={params['password']};Encrypt=no;TrustServerCertificate=Yes;"
        READ_QUERY = text("SELECT p.firstname, p.lastname, COUNT(*) \
                        FROM airportdb.passenger p, airportdb.booking b \
                        WHERE p.passenger_id = :passenger \
                        and p.passenger_id = b.passenger_id \
                        GROUP BY p.firstname, p.lastname")
        WRITE_QUERY = text("INSERT airportdb.booking (booking_id, flight_id, passenger_id, price, seat, stuff) \
                            SELECT next value for airportdb.booking_id, :flight, :passenger \
                            , 1000.00, '1A', convert (varbinary, stuff) FROM airportdb.booking WHERE booking_id = 100")
    elif db_type == 'ORACLE':
        DB_ENGINE=f"oracle+cx_oracle"
        params = {
            "host": os.environ.get('ORACLE_HOST', "localhost"),
            "database": os.environ.get('ORACLE_DB', "ORACLE_better_together"),
            "user": os.environ.get('ORACLE_USER', "admin"),
            "password": os.environ.get('ORACLE_PASS', "secret_password"),
            "port": os.environ.get('ORACLE_PORT', 1521),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}?encoding=UTF-8&nencoding=UTF-8"
        READ_QUERY = text("SELECT p.\"firstname\", p.\"lastname\", COUNT(*) \
                            FROM admin.\"passenger\" p, admin.\"booking\" b \
                            WHERE p.\"passenger_id\" = :passenger \
                            and p.\"passenger_id\" = b.\"passenger_id\" \
                            GROUP BY p.\"firstname\", p.\"lastname\"")
        WRITE_QUERY = text("INSERT into admin.\"booking\" (booking_id, flight_id, passenger_id, price, seat, stuff) \
                            SELECT nextval('booking_id'), :flight, :passenger \
                            , 1000.00, '1A', stuff FROM admin.\"booking\" WHERE booking_id = 100")
    elif db_type == 'POSTGRES':
        DB_ENGINE=f"postgresql+psycopg2"
        params = {
            "host": os.environ.get('POSTGRES_HOST', "localhost"),
            "database": os.environ.get('POSTGRES_DB', "db_name"),
            "user": os.environ.get('POSTGRES_USER', "admin1"),
            "password": os.environ.get('POSTGRES_PASS', "secret_password"),
            "port": os.environ.get('POSTGRES_PORT', 5432),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        READ_QUERY = text("SELECT p.firstname, p.lastname, COUNT(*) \
                        FROM airportdb.passenger p, airportdb.booking b \
                        WHERE p.passenger_id = :passenger \
                        and p.passenger_id = b.passenger_id \
                        GROUP BY p.firstname, p.lastname")
        WRITE_QUERY = text("INSERT into airportdb.booking (booking_id, flight_id, passenger_id, price, seat, stuff) \
                            SELECT nextval('booking_id'), :flight, :passenger \
                            , 1000.00, '1A', stuff FROM airportdb.booking WHERE booking_id = 100")
    elif db_type == 'AURORA_POSTGRES':
        DB_ENGINE=f"postgresql+psycopg2"
        params = {
            "host": os.environ.get('AURORA_POSTGRES_HOST', "localhost"),
            "host_ro": os.environ.get('AURORA_POSTGRES_READ_HOST', "localhost"),
            "database": os.environ.get('AURORA_POSTGRES_DB', "db_name"),
            "user": os.environ.get('AURORA_POSTGRES_USER', "admin"),
            "password": os.environ.get('AURORA_POSTGRES_PASS', "secret_password"),
            "port": os.environ.get('AURORA_POSTGRES_PORT', 5432),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        SQLALCHEMY_DATABASE_RW_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        SQLALCHEMY_DATABASE_RO_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host_ro']}:{params['port']}/{params['database']}"
        READ_QUERY = text("SELECT p.firstname, p.lastname, COUNT(*) \
                        FROM airportdb.passenger p, airportdb.booking b \
                        WHERE p.passenger_id = :passenger \
                        and p.passenger_id = b.passenger_id \
                        GROUP BY p.firstname, p.lastname")

        WRITE_QUERY = text("INSERT into airportdb.booking (booking_id, flight_id, passenger_id, price, seat, stuff) \
                            SELECT nextval('booking_id'), :flight, :passenger \
                            , 1000.00, '1A', stuff FROM airportdb.booking WHERE booking_id = 100")
    elif db_type == 'AURORA_MYSQL':
        DB_ENGINE=f"mysql+pymysql"
        params = {
            "host": os.environ.get('AURORA_MYSQL_HOST', "localhost"),
            "database": os.environ.get('AURORA_MYSQL_DB', "db_name"),
            "user": os.environ.get('AURORA_MYSQL_USER', "admin"),
            "password": os.environ.get('AURORA_MYSQL_PASS', "secret_password"),
            "port": os.environ.get('AURORA_MYSQL_PORT', 5432),
            "elasticache": os.environ.get('ELASTICACHE_HOST', 'localhost'),
        }
        SQLALCHEMY_DATABASE_URL = f"{DB_ENGINE}://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    try:
        # Create connection string and database engine 
        rdbms_engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=max_threads, max_overflow=50)
        rdbms_rw = create_engine(SQLALCHEMY_DATABASE_RW_URL, pool_size=max_threads, max_overflow=50)
        rdbms_rw.connect()
        # rdbms_ro = rdbms_rw
        rdbms_ro = create_engine(SQLALCHEMY_DATABASE_RO_URL, pool_size=max_threads, max_overflow=50)
        rdbms_ro.connect()
        cache_rw = Redis(host=params["elasticache"], port=os.environ.get('ELASTICACHE_PORT', 6379), decode_responses=False)
        cache_ro = Redis(host=params["elasticache"], port=os.environ.get('ELASTICACHE_PORT', 6379), read_from_replicas=True, decode_responses=False)
        elasticache = Redis(host=os.environ.get('ELASTICACHE_HOST'), port=os.environ.get('ELASTICACHE_PORT', 6379), decode_responses=True)
    except Exception as e:
        print("DB connect exception occurred")
        print(e)
        exit(1)
    return [rdbms_engine, rdbms_rw, rdbms_ro, cache_rw, cache_ro, WRITE_QUERY, READ_QUERY]
