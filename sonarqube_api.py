from sonarqube import SonarQubeClient

class SonarQube:

    def __init__(self, config: dict) -> None:
        username = config["username"]
        password = config["password"]
        sonarqube_url = config["url"]
        self.client = SonarQubeClient(username=username, password=password, sonarqube_url=sonarqube_url)

    # 获取项目列表
    def getProjects(self):
        projects=list(self.client.projects.search_projects())
        return projects

    # 获取项目
    def getProject(self,key):
        projects = self.getProjects()
        for i in range(len(projects)):
            if projects[i]['key'] == key:
                return projects[i]
        return None

    # 获取项目各个参数数据
    def getMeasures(self, component):
        metricKeys = "alert_status,bugs,,vulnerabilities,security_rating,code_smells,duplicated_lines_density,coverage,ncloc"
        measures = []
        measures.append(self.client.measures.get_component_with_specified_measures(
            component, metricKeys))
        return measures
    # 获取issue信息
    def getIssues(self, component):
        return list(self.client.issues.search_issues(componentKeys=component))

    def test(self):
        return self.client.metrics.search_metrics()

    def create_project(self, project_name):
        return self.client.projects.create_project(project=project_name, name=project_name, visibility="public")
    
    def delete_project(self, project_name):
        return self.client.projects.delete_project(project_name)

