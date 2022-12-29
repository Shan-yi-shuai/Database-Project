from database_api import *
from pjconfig import config
import pandas as pd
import datetime

database = Database(config["database"])

def time_converter(time_string):
    """
    根据输入的时间字符串，返回time类型的时间
    如果处理不了，则给出报错
    """
    if time_string == '':
        return datetime.datetime.now()
    try:
        # 处理YYYY-MM-DD HH:MM:SS格式
        time_type1 = datetime.datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
        return time_type1
    except ValueError:
        try:
            # 处理MMM DD, YYYY HH:MM:SS格式
            time_type2 = datetime.datetime.strptime(time_string, '%b %d, %Y %H:%M:%S')
            return time_type2
        except ValueError:
            try:
                # 处理%Y-%m-%dT%H:%M:%S格式
                time_type3 = datetime.datetime.strptime(time_string.split("+")[0], '%Y-%m-%dT%H:%M:%S')
                return time_type3
            except ValueError:
                # 处理其他格式
                raise ValueError('输入的时间格式不支持！')

def get_latest_version_id():
    all_version_id = database.select_all_version_id()
    all_version_id = [i['version_id'] for i in all_version_id]
    return max(all_version_id)

def get_oldest_version_id():
    all_version_id = database.select_all_version_id()
    all_version_id = [i['version_id'] for i in all_version_id]
    return min(all_version_id)

def analyse_by_type(issues):
    if len(issues) == 0:
        return
    all_types = database.select_all_type()
    type_dict = {}
    for type in all_types:
        type['sum'] = 0
        type_dict[type['type_id']] = type
    for issue in issues:
        type_dict[issue['type_id']]['sum'] += 1
    df_types = pd.DataFrame(all_types)
    # 全部信息
    print("---------------------Full detail---------------------")
    print(df_types)
    # rule
    print("---------------------Rule---------------------")
    print(df_types[['rule','sum']].groupby('rule').sum())
    # severity
    print("---------------------Severity---------------------")
    print(df_types[['severity','sum']].groupby('severity').sum())
    # type
    print("---------------------type---------------------")
    print(df_types[['type','sum']].groupby('type').sum())
def compute_issue_duration(issues):
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    all_cases = database.select_all_case()
    all_versions = database.select_all_version()
    case_dict = {}
    version_dict = {}
    for case in all_cases:
        case_dict[case['case_id']] = case
    for version in all_versions:
        version_dict[version['version_id']] = version
    for issue in issues:
        case = case_dict[issue['case_id']]
        start_time = version_dict[case['version_new']]['commit_time']
        end_time = time if case['version_disappear'] is None else version_dict[case['version_disappear']]['commit_time']
        end_time = time_converter(end_time)
        issue['duration'] = end_time - datetime.datetime.strptime(start_time.split("+")[0], '%Y-%m-%dT%H:%M:%S')
    return issues
def analyse_by_time(issues):
    if len(issues) == 0:
        return
    df_issue = pd.DataFrame(issues)
    # 需要展示哪些信息呢？
    print(df_issue[['instance_id','file_path','description','duration']].sort_values(by='duration'))

def analyse_by_type_time(issues):
    if len(issues) == 0:
        return
    df_issue = pd.DataFrame(issues)
    print('---------------------duration---------------------')
    print(df_issue.groupby('type_id').agg({'duration': ['mean', 'median']}))

def analyse_latest_version(method):
    latest_version_id = get_latest_version_id()
    issues = database.select_issues_by_version(latest_version_id)
    issues = compute_issue_duration(issues)
    if method == 'type':
        analyse_by_type(issues)
    elif method == 'time':
        analyse_by_time(issues)
    elif method == 'type_time':
        analyse_by_type_time(issues)


def analyse_any_version(commit_hash,method=0):
    version = database.select_version_commit_hash(commit_hash)
    all_cases = database.select_all_case()
    issues = database.select_issues_by_version(version['version_id'])
    issues = compute_issue_duration(issues)
    case_dict = {}
    for case in all_cases:
        case_dict[case['case_id']] = case
    for issue in issues:
        issue['case_status'] = case_dict[issue['case_id']]['case_status']
    df_issues = pd.DataFrame(issues)
    # 引入
    print('%%%%%%%%%%%%%%%%%%%%%Issue introduce%%%%%%%%%%%%%%%%%%%%%')
    open_issues = df_issues[df_issues['case_status'] == 'OPEN'].to_dict(orient='records')
    analyse_by_type(open_issues)
    # 消除
    print('%%%%%%%%%%%%%%%%%%%%%Issue eliminate%%%%%%%%%%%%%%%%%%%%%')
    close_issues = df_issues[df_issues['case_status'] == 'CLOSED'].to_dict(orient='records')
    analyse_by_type(close_issues)
    analyse_by_time(close_issues)
    analyse_by_type_time(close_issues)

def analyse_any_period(start_time,end_time):
    start_time = time_converter(start_time)
    end_time = time_converter(end_time)
    all_version = database.select_all_version()
    version_start = get_oldest_version_id()
    version_end = get_latest_version_id()
    sorted_version = sorted(all_version, key=lambda x: x['version_id'], reverse=False)
    for version in sorted_version:
        if time_converter(version['commit_time']) >= start_time:
            version_start = version['version_id']
            break;
    sorted_version = sorted(all_version, key=lambda x: x['version_id'], reverse=True)
    for version in sorted_version:
        if time_converter(version['commit_time']) <= end_time:
            version_end = version['version_id']
            break;
    all_issue = database.select_all_issue()
    df_issue = pd.DataFrame(all_issue)
    period_issue = df_issue[df_issue['version_id'].isin(list(range(version_start,version_end+1)))].to_dict(orient='records')
    period_issue = compute_issue_duration(period_issue)
    analyse_by_type(period_issue)
    analyse_by_time(period_issue)
    analyse_by_type_time(period_issue)



# analyse_latest_version('new_version','type_time')
# analyse_any_version('7f9bc054f1c649a30aaea66376607352e6daec31')
analyse_any_period('2022-12-05T15:47:11+08:00','')