import sys
import time
from pjconfig import config
from sonarqube_api import *
from database_api import *
from match.location_processor import *

database = Database(config["database"])

# sonarqube
s = SonarQube(config["sonarqube"])
for i in range(30):
    issues = s.getIssues(config["sonar_project_name"])
    if len(issues) > 0:
        break
    time.sleep(0.1)
print("issues:", len(issues))


version_id = database.insert_version(sys.argv[1], sys.argv[2], sys.argv[3])
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