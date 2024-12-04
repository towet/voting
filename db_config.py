from flask_mysqldb import MySQL

def init_db(app):
    # MySQL configurations
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'voting'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    # Initialize MySQL
    mysql = MySQL(app)
    return mysql

def get_db():
    from flask import current_app
    return current_app.mysql