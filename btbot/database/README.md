# database
You can build up your MySQL database through files in this folder.

## Set Up Database
First you need to install MySQL
```buildoutcfg
sudo apt update
sudo apt install mysql-server
```
Then, you need to login to set up configuration.
```buildoutcfg
sudo mysql -u root
```
Then, change the password
```buildoutcfg
mysql> ALTER USER 'root'@'localhost' IDENTIFIED BY 'password';
```
If you wanna use users other than root, do the followings
```buildoutcfg
mysql> CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';
# You need to give permission to new user
mysql> GRANT ALL PRIVILEGES ON *.* TO 'username'@'localhost' IDENTIFIED BY 'password';
```
Next, you need to install python interface. You need to use `MySQLdb` in this implementation.
```
sudo apt install libmysqlclient-dev
pip install mysqlclient
```

In `config.py`, there are some parameters like password and username.
Depending on your setup, you need to change the file.

## Create database
```buildoutcfg
python sql_declarative.py
```

## Store data into the database
```buildoutcfg
python store.py
```