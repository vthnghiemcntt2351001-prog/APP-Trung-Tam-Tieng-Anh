# Cho phép Django 6.1 tương thích và kết nối mượt mà với MySQL 8.0
try:
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseFeatures.minimum_database_version = property(lambda self: (8, 0))
except ImportError:
    pass
