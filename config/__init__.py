import sys

# Patch MySQLdb with PyMySQL to work on Vercel without requiring mysqlclient build headers
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Bypass MySQL version check (MySQL 5.6 compatibility for Django 4.2+)
try:
    from django.db.backends.mysql.base import DatabaseWrapper
    DatabaseWrapper.check_database_version_supported = lambda self: None
except ImportError:
    pass
