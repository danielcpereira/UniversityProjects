## DB TABLES

docker exec -it ss_practical_project-db-1 psql -U postgres -d docdb


docdb=# \dt (To list all tables)

docdb=# \d audit_logs (To check a table structure)

docdb=# SELECT * FROM audit_logs; (To view a full table)

docdb-# \q (To quit)