from sonarqube import SonarQubeClient
# import sonarqube as sonar



class SonarQube:

    def __init__(self,url="http://localhost:9000",username="admin",password="123") -> None:
        username = username
        password = password
        sonarqube_url = url
        self.client = SonarQubeClient(username=username, password=password,
                                 sonarqube_url=sonarqube_url)

    # 获取项目列表
    def getProjects(self):
        projects=list(self.client.projects.search_projects())
        return projects

    # 获取项目各个参数数据
    def getMeasures(self, component):
        metricKeys = "alert_status,bugs,,vulnerabilities,security_rating,code_smells,duplicated_lines_density,coverage,ncloc"
        measures = []
        measures.append(self.client.measures.get_component_with_specified_measures(
            component, metricKeys))
        return measures
    # 获取issue信息
    def getIssues(self, component):
        return list(s.client.issues.search_issues(componentKeys=component))



s = SonarQube()
all_project_info = s.getProjects()
for project_info in all_project_info:
    component = project_info.get("key")
    b = s.getMeasures(component)
    # 获取所有issues的信息
    issues = s.getIssues(component)
    # print(b)
    print(issues[0],issues[1])
