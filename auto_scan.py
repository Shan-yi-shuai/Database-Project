import git
import os
import shutil

repo_path = "../test-repo-for-database-pj"
repo = git.Repo(repo_path)
repo_name = "pj_repo"
commit_list = []
for commit in repo.iter_commits():
    commit_list.insert(0,commit.hexsha)
    # print(commit.hexsha)
    # print(commit.message)
    # print(commit.author.name)
    # print(commit.authored_datetime)
for index, commit_sha in enumerate(commit_list):
    os.mkdir("commit_file")
    repo.git.checkout(commit_sha)
    commit = repo.commit(commit_sha)
    print('---------------------------------')
    for file, lines in commit.stats.files.items():
        # 感觉git commit文件这里可能还有点问题，我处理的比较粗糙
        if "=> " in file:
            file = file.split("=> ")[1]
        # {hifigan => vocoder/hifigan}/config_16k_.json
        file.replace('}','')
        if ' ' in file:
            continue
        file = repo_path + '/' + file
     
        if os.path.exists(file):
            shutil.copy(file, "commit_file")
    os.chdir("commit_file")
    os.system("sonar-scanner -D sonar.projectKey=%s_commit%d"% (repo_name,index))
    os.chdir("..")
    shutil.rmtree("commit_file")