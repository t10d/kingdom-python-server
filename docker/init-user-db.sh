#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER tester;
    CREATE DATABASE court;
    GRANT ALL PRIVILEGES ON DATABASE court TO tester;
EOSQL
