from collections import defaultdict
import json
import git
import os
import shutil
from pjconfig import config
from sonarqube_api import SonarQube

repo_dir = config["repo_dir"]
repo = git.Repo(repo_dir)
sonar = SonarQube(config["sonarqube"])

commit_list = []
for commit in repo.iter_commits():
    commit_list.insert(0,commit.hexsha)
    # print(commit.hexsha)
    # print(commit.message)
    # print(commit.author.name)
    # print(commit.authored_datetime)

for index, commit_sha in enumerate(commit_list):
    project_name = config["sonar_project_name"]
    try:
        sonar.create_project(project_name)
    except:
        pass
    repo.git.checkout(commit_sha)
    commit = repo.commit(commit_sha)
    print('---------------------------------')
    if index == 0:
        shutil.copytree(repo_dir, "commit_file")
    else:
        os.mkdir("commit_file")
        file_changes = defaultdict(list)
        for diff in commit.diff("Head~1"):
            if diff.change_type == 'A':
                file_changes['delete'].append(diff.b_blob.path)
                continue
            elif diff.change_type == 'D':
                file_changes['add'].append(diff.a_blob.path)
                file_to_copy = diff.a_blob.path
            elif diff.change_type == 'M':
                file_changes['modify'].append(diff.b_blob.path)
                file_to_copy = diff.b_blob.path
            elif diff.change_type == 'R':
                file_changes['rename'].append((diff.a_blob.path, diff.b_blob.path))
                file_to_copy = diff.a_blob.path
            path = "./commit_file/" + file_to_copy
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            shutil.copy(repo_dir + file_to_copy, path)
        with open('changed_files.txt', 'w') as f:
            json.dump(file_changes, f)
    os.chdir("commit_file")
    os.system(config["sonar_scanner_cmd"] % project_name)
    os.chdir("..")
    os.system("python add_to_database.py %s %s %s" % (commit_sha, commit.committed_datetime.isoformat(), commit.committer))
    shutil.rmtree("commit_file")
    sonar.delete_project(project_name)
    os.system("python match_case.py %s" % (index + 1))