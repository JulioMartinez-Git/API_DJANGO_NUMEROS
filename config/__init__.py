import sys

# Patch MySQLdb with PyMySQL to work on Vercel without requiring mysqlclient build headers
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
