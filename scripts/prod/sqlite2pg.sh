#!/bin/sh

# https://gist.github.com/typpo/5282536

# This script will migrate schema and data from a SQLite3 database to PostgreSQL.
# Schema translation based on http://stackoverflow.com/a/4581921/1303625.
# Some column types are not handled (e.g blobs).

if [ $# -lt 3 ]; then
  echo "usage: sqlite2pg.sh sqlite_db_path pg_db_name pg_user_name";
  exit 1
fi

SQLITE_DB_PATH=$1
PG_DB_NAME=$2
PG_USER_NAME=$3

SQLITE_DUMP_FILE="sqlite_data.sql"

sqlite3 $SQLITE_DB_PATH .dump > $SQLITE_DUMP_FILE

# PRAGMAs are specific to SQLite3.
sed -i '/PRAGMA/d' $SQLITE_DUMP_FILE
# Convert sequences.
sed -i '/sqlite_sequence/di ; s/integer PRIMARY KEY AUTOINCREMENT/serial PRIMARY KEY/ig' $SQLITE_DUMP_FILE
# Convert column types.
sed -i 's/datetime/timestamp/ig ; s/integer[(][^)]*[)]/integer/ig ; s/text[(]\([^)]*\)[)]/varchar(\1)/ig' $SQLITE_DUMP_FILE
# Convert reserved keywords
sed -i 's/TABLE user/TABLE "user"/gi; s/REFERENCES user/REFERENCES "user"/gi' $SQLITE_DUMP_FILE

#createdb -U $PG_USER_NAME $PG_DB_NAME
psql $PG_DB_NAME $PG_USER_NAME < $SQLITE_DUMP_FILE

# Update Postgres sequences.
psql $PG_DB_NAME $PG_USER_NAME -c "\ds" | grep sequence | cut -d'|' -f2 | tr -d '[:blank:]' |
while read sequence_name; do
  table_name=${sequence_name%_id_seq}

  psql $PG_DB_NAME $PG_USER_NAME -c "select setval('$sequence_name', (select max(id) from $table_name))"
done
