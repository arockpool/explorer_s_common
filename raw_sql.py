from django.db import connection, connections


def exec_sql(sql, params=None, database="default"):
    cursor = connections[database].cursor()
    cursor.execute(sql, params)
    return cursor.fetchall()
