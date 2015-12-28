## Testing postgres
* Install psycopg2

`sudo apt-get install libpq-dev python-dev`

## Testing mysql
* Install the prerequisites.

`sudo apt-get install libmysqlclient-dev`
`pip install mysql-python`

* Launch a mysql instance, or use a docker run command below. Remember to edit bind-address in mysql_test.conf to the host's docker IP address.
`docker run -d --name mysql-test-server -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=test -v $PWD/instrumentor_/mysql_test.cnf  mysql:5.6`

* Launch the test as shown below.
`python -m unittest instrumentor_.mysql_test_disabled`
