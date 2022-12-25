from pjconfig import config
from sonarqube_api import *
from database_api import *
from match.location_processor import *


# 获取创建表的sql语句
sql_create_issue_type = get_create_sql('sql/create_issue_type.txt')
sql_create_issue_instance = get_create_sql('sql/create_issue_instance.txt')
sql_create_issue_location = get_create_sql('sql/create_issue_location.txt')
sql_create_issue_case = get_create_sql('sql/create_issue_case.txt')
sql_create_issue_match = get_create_sql('sql/create_issue_match.txt')
sql_create_version = get_create_sql('sql/create_version.txt')
# 创建数据库
database = Database(config["database"])
# 创建数据表
database.create_table(sql_create_issue_type,'issue_type')
database.create_table(sql_create_version,'version')
database.create_table(sql_create_issue_instance,'issue_instance')
database.create_table(sql_create_issue_location,'issue_location')
database.create_table(sql_create_issue_case,'issue_case')
database.create_table(sql_create_issue_match,'issue_match')

# sonarqube
s = SonarQube(config["sonarqube"])
issues = s.getIssues(config["sonar_project_name"])

version_id = database.insert_version(issues[0])
issue_location_dict = dict()
for issue in issues:
    issue_type_id = database.insert_issue_type(issue)
    issue_instance_id = database.insert_issue_instance(issue, issue_type_id,version_id)
    database.insert_issue_location(issue, issue_instance_id, issue_location_dict)

for file_path in issue_location_dict:
    processor = LocationProcessor(config["repo_dir"] + file_path)
    for raw_location in issue_location_dict[file_path]:
        location = processor.process(raw_location)
        database.update_issue_location(location.id,['code', 'records','include_records'],[location.code,location.records,location.include_records])
    