from database_api import *
from pjconfig import config
import pandas as pd
import datetime
import sys

database = Database(config["database"])
pd.set_option('expand_frame_repr', False)
# pd.set_option('display.max_rows', 20) # 设置每页最大行数

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
    print("---------------------All instance---------------------")
    print(pd.DataFrame(issues))
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
        issue['duration'] = (end_time - datetime.datetime.strptime(start_time.split("+")[0], '%Y-%m-%dT%H:%M:%S'))
        # print(issue['duration'],type(issue['duration']))
    return issues
def analyse_by_time(issues):
    if len(issues) == 0:
        return
    df_issue = pd.DataFrame(issues)
    # 需要展示哪些信息呢？
    print('---------------------duration---------------------')
    print(df_issue[['instance_id','file_path','description','duration']].sort_values(by='duration'))

def analyse_by_type_time(issues):
    if len(issues) == 0:
        return
    df_issue = pd.DataFrame(issues)
    print('---------------------duration---------------------')
    # print(df_issue.groupby('type_id').agg({'duration': ['mean', 'median']}),type(df_issue.groupby('type_id').agg({'duration': ['mean', 'median']})))
    df_group = df_issue.groupby('type_id').agg({'duration': ['mean', 'median']})
    # print(df_group)
    mean_list = []
    median_list = []
    type_id_list = list(set(df_issue['type_id']))
    for index,row in df_group['duration', 'mean'].iteritems():
        mean_list.append(str(row).split('.')[0])
    for index,row in df_group['duration', 'median'].iteritems():
        median_list.append(str(row).split('.')[0]) 
    print(pd.DataFrame(list(zip(type_id_list,mean_list,median_list)),columns=['type_id','mean','median']))

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
    # df_issues = pd.DataFrame(issues)
    # 引入
    print('%%%%%%%%%%%%%%%%%%%%%Issue introduce%%%%%%%%%%%%%%%%%%%%%')
    open_case = database.select_case_by_version_new(version['version_id'])
    open_issue_list = []
    for case in open_case:
        open_issue_list.append(database.select_instance_by_version_case(version['version_id'],case['case_id'])[0])
    # open_issues = df_issues[df_issues['case_status'] == 'OPEN'].to_dict(orient='records')
    # print(open_issue_list)
    analyse_by_type(open_issue_list)
    # 消除
    print('%%%%%%%%%%%%%%%%%%%%%Issue eliminate%%%%%%%%%%%%%%%%%%%%%')
    # close_issues = df_issues[df_issues['case_status'] == 'CLOSED'].to_dict(orient='records')
    close_case = database.select_case_by_version_disappear(version['version_id'])
    close_issue_list = []
    for case in close_case:
        issues = database.select_issues_by_case(case['case_id'])
        issues = sorted(issues, key=lambda x: x['version_id'], reverse=True)
        close_issue_list.append(issues[0])
    close_issue_list = compute_issue_duration(close_issue_list)
    analyse_by_type(close_issue_list)
    analyse_by_time(close_issue_list)
    analyse_by_type_time(close_issue_list)

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
    all_cases = database.select_all_case()
    case_dict = {}
    for case in all_cases:
        case_dict[case['case_id']] = case
    for issue in period_issue:
        issue['case_status'] = case_dict[issue['case_id']]['case_status']
    df_issues = pd.DataFrame(period_issue)
    # 引入
    print('%%%%%%%%%%%%%%%%%%%%%Issue introduce%%%%%%%%%%%%%%%%%%%%%')
    open_case = []
    for i in range(version_start,version_end+1):
        open_case += database.select_case_by_version_new(i)
    open_issue_list = []
    for case in open_case:
        issues = database.select_issues_by_case(case['case_id'])
        issues = sorted(issues, key=lambda x: x['version_id'], reverse=False)
        open_issue_list.append(issues[0])
    analyse_by_type(open_issue_list)
    # open_issues = df_issues[df_issues['case_status'] == 'OPEN'].to_dict(orient='records')
    # analyse_by_type(open_issues)
    # 消除
    print('%%%%%%%%%%%%%%%%%%%%%Issue eliminate%%%%%%%%%%%%%%%%%%%%%')
    close_case = []
    for i in range(version_start,version_end+1):
        close_case += database.select_case_by_version_disappear(i)
    close_issue_list = []
    for case in close_case:
        issues = database.select_issues_by_case(case['case_id'])
        issues = sorted(issues, key=lambda x: x['version_id'], reverse=True)
        close_issue_list.append(issues[0])
    close_issue_list = compute_issue_duration(close_issue_list)
    analyse_by_type(close_issue_list)
    analyse_by_time(close_issue_list)
    analyse_by_type_time(close_issue_list)

def analyse_committer_period(committer,start_time,end_time):
    start_time = time_converter(start_time)
    end_time = time_converter(end_time)
    all_version = database.select_all_version()
    version_dict = {}
    for version in all_version:
        version_dict[version['version_id']] = version
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
    version_list = []
    for i in range(version_start,version_end+1):
        if all_version[i-1]['committer'] == committer:
            version_list.append(all_version[i-1]['version_id'])
    # 引入
    print('%%%%%%%%%%%%%%%%%%%%%Issue introduce%%%%%%%%%%%%%%%%%%%%%')
    open_case = []
    for i in version_list:
        open_case += database.select_case_by_version_new(i)
    open_issue_list = []
    for case in open_case:
        issues = database.select_issues_by_case(case['case_id'])
        issues = sorted(issues, key=lambda x: x['version_id'], reverse=False)
        open_issue_list.append(issues[0])
    analyse_by_type(open_issue_list)
    # open_issues = df_issues[df_issues['case_status'] == 'OPEN'].to_dict(orient='records')
    # analyse_by_type(open_issues)
    # 消除
    print('%%%%%%%%%%%%%%%%%%%%%Issue eliminate%%%%%%%%%%%%%%%%%%%%%')
    close_case = []
    for i in version_list:
        close_case += database.select_case_by_version_disappear(i)
    close_issue_list = []
    for case in close_case:
        issues = database.select_issues_by_case(case['case_id'])
        issues = sorted(issues, key=lambda x: x['version_id'], reverse=True)
        issue = issues[0]
        issue['committer'] = version_dict[issue['version_id']]['committer']
        close_issue_list.append(issues[0])
    close_issue_list = compute_issue_duration(close_issue_list)
    analyse_by_type(close_issue_list)
    analyse_by_time(close_issue_list)
    analyse_by_type_time(close_issue_list)
    # all_issue = database.select_all_issue()
    # df_issue = pd.DataFrame(all_issue)
    # period_issue = df_issue[df_issue['version_id'].isin(version_list)].to_dict(orient='records')
    # period_issue = compute_issue_duration(period_issue)
    # analyse_by_type(period_issue)
    # analyse_by_time(period_issue)
    # analyse_by_type_time(period_issue)

def analyse_case(case_id):
    issues = database.select_issues_by_case(case_id)
    # 从早到晚展示一个issue的具体信息
    for issue in issues:
        locations = database.select_locations_by_instance(issue['instance_id'])
        print('---------------------instance_information---------------------')
        print(pd.DataFrame(issue,index=[0])[['instance_id','description']])
        print('---------------------location---------------------')
        print(pd.DataFrame(locations)[['file_path','start_line','end_line','start_offset','end_offset']])
    
def analyse_instance(instance_id):
    instance = database.select_instance_by_id(instance_id)
    print('---------------------instance---------------------')
    print(pd.DataFrame(instance,index=[0]))
    # location
    # committer
def analyse_version(version_id=0):
    if version_id == 0:
        all_version = database.select_all_version()
        print('---------------------All version---------------------')
        print(pd.DataFrame(all_version))
    else:
        version = database.select_version_by_id(version_id)
        print('---------------------version---------------------')
        print(pd.DataFrame(version,index=[0]))

def analyse(mode,arg_list):
    if mode == 'latest-version':
        analyse_latest_version(arg_list[0])
    elif mode == 'any-version':
        analyse_any_version(arg_list[0])
    elif mode == 'period':
        analyse_any_period(arg_list[0],arg_list[1])
    elif mode == 'committer-period':
        analyse_committer_period(arg_list[0],arg_list[1],arg_list[2])
    elif mode == 'case':
        analyse_case(arg_list[0])
    elif mode == 'version':
        analyse_version(arg_list[0])
    else: print('wrong command!')

# print(pd.options.display.max_rows)
mode = sys.argv[1]
arg_list = sys.argv[2:len(sys.argv)] + ['']
analyse(mode,arg_list)