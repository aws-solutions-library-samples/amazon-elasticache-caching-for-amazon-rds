#### Developer Notes

```bash
# Export dataset
mysqldump -h ${MYSQL_HOST} -P ${MYSQL_PORT} -u ${MYSQL_USER} --databases ${MYSQL_DB} > ${MYSQL_DB}.sql
mysqldump --compress -h ${MYSQL_HOST} -P ${MYSQL_PORT} -u ${MYSQL_USER} --databases ${MYSQL_DB} > ${MYSQL_DB}.sql
gzip -9 -k ${MYSQL_DB}.sql
bzip2 -9 -k ${MYSQL_DB}.sql
# Import dataset
source .env.sh
gunzip ${MYSQL_DB}.sql.gz
mysql -h ${MYSQL_HOST} -P ${MYSQL_PORT}  -u ${MYSQL_USER} -p${MYSQL_PASS} -e "CREATE DATABASE ${MYSQL_DB}_new;"
mysql -h ${MYSQL_HOST} -P ${MYSQL_PORT}  -u ${MYSQL_USER} -p${MYSQL_PASS} "${MYSQL_DB}_new" < ${MYSQL_DB}.sql
```