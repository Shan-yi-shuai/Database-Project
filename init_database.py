from pjconfig import config
from database_api import *

# 获取创建表的sql语句
sql_create_issue_type = get_create_sql('sql/create_issue_type.txt')
sql_create_issue_instance = get_create_sql('sql/create_issue_instance.txt')
sql_create_issue_location = get_create_sql('sql/create_issue_location.txt')
sql_create_issue_case = get_create_sql('sql/create_issue_case.txt')
sql_create_version = get_create_sql('sql/create_version.txt')
# 创建数据库
database = Database(config["database"])
# 创建数据表
database.create_table(sql_create_issue_type,'issue_type')
database.create_table(sql_create_version,'version')
database.create_table(sql_create_issue_instance,'issue_instance')
database.create_table(sql_create_issue_location,'issue_location')
database.create_table(sql_create_issue_case,'issue_case')
