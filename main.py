from sonarqube_api import *
from database_api import *


# 获取数据库配置
config = get_config('./config.txt')
# 读取数据
# room_data = pd.read_csv('room.csv',encoding="gbk",keep_default_na=False)
# student_data = pd.read_csv('student.csv',keep_default_na=False)
# 获取创建表的sql语句
sql_create_issue_type = get_create_sql('sql/create_issue_type.txt')
sql_create_issue_instance = get_create_sql('sql/create_issue_instance.txt')
sql_create_issue_location = get_create_sql('sql/create_issue_location.txt')
sql_create_issue_case = get_create_sql('sql/create_issue_case.txt')
sql_create_issue_match = get_create_sql('sql/create_issue_match.txt')
sql_create_version = get_create_sql('sql/create_version.txt')
# 创建数据库
database = Database(config)
# 创建数据表
database.create_table(sql_create_issue_type,'issue_type')
database.create_table(sql_create_version,'version')
database.create_table(sql_create_issue_instance,'issue_instance')
database.create_table(sql_create_issue_location,'issue_location')
database.create_table(sql_create_issue_case,'issue_case')
database.create_table(sql_create_issue_match,'issue_match')

# sonarqube
s = SonarQube()
# project = s.getProject('test')
issues = s.getIssues('pj_repo')
version_id = database.insert_version(issues[0])
for issue in issues:
    issue_type_id = database.insert_issue_type(issue)
    issue_instance_id = database.insert_issue_instance(issue, issue_type_id,version_id)
    database.insert_issue_location(issue,issue_instance_id)
    