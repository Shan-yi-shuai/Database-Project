import pymysql
import datetime
from pymysql.converters import escape_string
from match.issue import *

class Database:
    def __init__(self, config:dict):
        try:
            self.conn = pymysql.connect(**config)
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            self.log = Log()
        except Exception as e:
            print(type(e),e)
    # 强制删除
    def force_delete(self,table_name):
        try:
            self.cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
            sql_delete = "DROP TABLE IF EXISTS " + table_name
            self.cursor.execute(sql_delete)
            self.cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        except Exception as e:
            print(type(e),e)
            self.log.make_new_log(str(e),sql_delete)
    # 创建数据表
    def create_table(self,sql,table_name):
        self.force_delete(table_name)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(type(e),e)
            print(sql)
            self.log.make_new_log(str(e),sql)
            # 发生错误时回滚
            self.conn.rollback()
    # 执行sql语句
    def execute(self,sql):
        try:
            result = self.cursor.execute(sql)
            return result
        except Exception as e:
            print(type(e),e)
            # print(sql)
            self.log.make_new_log(str(e),sql)
            return e
    def to_sql(self,value):
        if type(value) == int:
            return str(value)
        if type(value) == bool:
            return str(value)
        if value == 'null':
            return value
        if type(value) == str:
            value = escape_string(value)
            return "'%s'" % value
        if type(value) == list:
            value = ','.join('None' if value == None else value  for value in value)
            return "'%s'" % value
        return value
    # 插入数据
    def insert_issue_location(self, issue, instance_id, res: dict):
        table_name = 'issue_location'
        table_key = ['instance_id','file_path','class','method','start_line','end_line','start_offset','end_offset','code','msg']
        key_str = ','.join(table_key)
        if len(issue['flows']) != 0:
            for i in range(len(issue['flows'])):
                locations = issue['flows'][i]['locations'][0]
                value = [instance_id,locations['component'],'null', 'null',locations['textRange']['startLine'], locations['textRange']['endLine'], locations['textRange']['startOffset'], locations['textRange']['endOffset'], 'null', locations['msg']]
                value_str = ','.join(self.to_sql(value) for value in value)
                sql = "insert into %s(%s) values(%s)" %(table_name, key_str, value_str)
                result = self.execute(sql)
                location_id = self.cursor.lastrowid
                if result != True:
                    self.conn.rollback()
                    return False
                self.conn.commit()
                file_path = locations['component'].split(":")[1]
                if file_path not in res:
                    res[file_path] = []
                res[file_path].append(RawIssueLocation(location_id, file_path, locations['textRange']['startLine'], locations['textRange']['endLine'], locations['textRange']['startOffset'], locations['textRange']['endOffset']))
        else:
            value = [instance_id,issue['component'],'null', 'null',issue['textRange']['startLine'], issue['textRange']['endLine'], issue['textRange']['startOffset'], issue['textRange']['endOffset'], 'null', 'null']
            value_str = ','.join(self.to_sql(value) for value in value)
            sql = "insert into %s(%s) values(%s)" %(table_name, key_str, value_str)
            result = self.execute(sql)
            if result != True:
                self.conn.rollback()
                return False
            self.conn.commit()
            location_id = self.cursor.lastrowid
            file_path = issue['component'].split(":")[1]
            if file_path not in res:
                res[file_path] = []
            res[file_path].append(RawIssueLocation(location_id, file_path, issue['textRange']['startLine'], issue['textRange']['endLine'], issue['textRange']['startOffset'], issue['textRange']['endOffset']))
        return True
    
    def update_issue_location(self, location_id, table_key:list, value:list):
        table_name = 'issue_location'
        # key_str = ','.join(table_key)
        # value_str = ','.join(self.to_sql(value) for value in value)
        for i in range(len(table_key)):
            key_str = table_key[i]
            value_str = self.to_sql(value[i])
            sql = "update %s set %s = %s where location_id = %d" %(table_name, key_str, value_str, location_id)
            result = self.execute(sql)
            if result != True:
                self.conn.rollback()
                return False
        self.conn.commit()
        return True

    def insert_issue_instance(self,issue,type_id,version_id):
        table_name = 'issue_instance'
        table_key = ['type_id','version_id','commit_hash','file_path','description']
        key_str = ','.join(table_key)
        value = [type_id,version_id,issue['hash'],issue['component'],issue['message']]
        value_str = ','.join(self.to_sql(value) for value in value)
        sql = "insert into %s(%s) values(%s)" %(table_name, key_str, value_str)
        result = self.execute(sql)
        id = self.cursor.lastrowid
        if result != True:
            self.conn.rollback()
            return -1
        self.conn.commit()
        return id
    
    def insert_issue_type(self,issue):
        table_name = 'issue_type'
        table_key = ['rule','severity','type','scope','quickFixAvailable']
        key_str = ','.join(table_key)
        value = [issue['rule'],issue['severity'],issue['type'],issue['scope'],issue['quickFixAvailable']]
        value_str = ','.join(self.to_sql(value) for value in value)
        # 先判断是否存在
        sql_select = "select * from issue_type where (%s) = (%s)" %(key_str, value_str)
        # sql_select = 'select * from issue_type'
        self.cursor.execute(sql_select)
        result = self.cursor.fetchall()
        if len(result) != 0:
            return result[0]['type_id']
        sql_insert = "insert into %s(%s) values(%s)" %(table_name, key_str, value_str)
        result = self.execute(sql_insert)
        if result != True:
            self.conn.rollback()
            return -1
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_version(self, hash, time, committer):
        table_name = 'version'
        table_key = ['commit_hash','commit_time','committer']
        key_str = ','.join(table_key)
        value = [hash, time, committer]
        value_str = ','.join(self.to_sql(value) for value in value)
        sql = "insert into %s(%s) values(%s)" %(table_name, key_str, value_str)
        result = self.execute(sql)
        id = self.cursor.lastrowid
        if result != True:
            self.conn.rollback()
            return -1
        self.conn.commit()
        return id
    
    def select_issue_instance(self, keys, values):
        sql = "select * from issue_instance where (%s)=(%s)" % (','.join(keys), ','.join(self.to_sql(v) for v in values))
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def select_issue_location(self, keys, values):
        sql = "select * from issue_location where (%s)=(%s)" % (','.join(keys), ','.join(self.to_sql(v) for v in values))
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def insert_issue_case(self, iss_inst):
        table_name = 'issue_case'
        table_key = ['type_id','version_new','case_status']
        key_str = ','.join(table_key)
        value = [iss_inst["type_id"], iss_inst["version_id"], "OPEN"]
        value_str = ','.join(self.to_sql(value) for value in value)
        sql = "insert into %s(%s) values(%s)" %(table_name, key_str, value_str)
        result = self.execute(sql)
        id = self.cursor.lastrowid
        if result != True:
            self.conn.rollback()
            return -1
        self.conn.commit()
        return id
    
    def update_issue_instance_case(self, instance_id, case_id):
        sql = "update issue_instance set case_id = %s where instance_id = %d" % (case_id, instance_id)
        result = self.execute(sql)
        if result != True:
            self.conn.rollback()
            return False
        self.conn.commit()
        return True
    
    def close_issue_case(self, case_id, version_disappear):
        sql = "update issue_case set version_disappear=%s,case_status='CLOSED' where case_id = %s" % (version_disappear, case_id)
        result = self.execute(sql)
        if result != True:
            self.conn.rollback()
            return False
        self.conn.commit()
        return True
    
    def match_issue_case(self, o_inst_id, n_inst_id):
        sql = "UPDATE issue_instance SET case_id = (SELECT case_id FROM issue_instance WHERE instance_id = %s) WHERE instance_id = %s" % (o_inst_id, n_inst_id)
        result = self.execute(sql)
        if result != True:
            self.conn.rollback()
            return False
        self.conn.commit()
        return True

    def insert_match(self,match):
        True
    
    def insert_case(self,match):
        True

    def select_version_commit_hash(self,commit_hash):
        table_name = 'version'
        commit_hash = self.to_sql(commit_hash)
        sql = "select * from %s where commit_hash = %s"%(table_name,commit_hash)
        self.execute(sql)
        return self.cursor.fetchone()
    
    def select_issues_by_version(self,version_id):
        table_name = 'issue_instance'
        version_id = self.to_sql(version_id)
        sql = "select * from %s where version_id = %s"%(table_name,version_id)
        self.execute(sql)
        return self.cursor.fetchall()
    
    def select_locations_by_instance(self,instance_id):
        table_name = 'issue_location'
        instance_id = self.to_sql(instance_id)
        sql = "select * from %s where instance_id = %s"%(table_name,instance_id)
        self.execute(sql)
        return self.cursor.fetchall()
    
    def select_issues_by_case(self,case_id):
        table_name = 'issue_instance'
        case_id = self.to_sql(case_id)
        sql = "select * from %s where case_id = %s"%(table_name,case_id)
        self.execute(sql)
        return self.cursor.fetchall()
    
    def select_all_version_id(self):
        table_name = 'issue_instance'
        sql = "select version_id from %s "%(table_name)
        self.execute(sql)
        return self.cursor.fetchall()
    
    def select_all_issue(self):
        table_name = 'issue_instance'
        sql = "select * from %s "%(table_name)
        self.execute(sql)
        return self.cursor.fetchall()

    def select_all_type(self):
        table_name = 'issue_type'
        sql = "select * from %s "%(table_name)
        self.execute(sql)
        return self.cursor.fetchall()

    def select_all_case(self):
        table_name = 'issue_case'
        sql = "select * from %s "%(table_name)
        self.execute(sql)
        return self.cursor.fetchall()

    def select_all_version(self):
        table_name = 'version'
        sql = "select * from %s "%(table_name)
        self.execute(sql)
        return self.cursor.fetchall()
    
# 日志：记录报错以及解决方案
class Log:
    def __init__(self) -> None:
        self.file = open('log.txt','w')
    
    def get_time(self):
        now_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(now_time,'%Y-%m-%d %H:%M:%S')
        return time_str

    def make_new_log(self,message,sql):
        time = self.get_time()
        self.file.write(time + '\n')
        self.file.write('error:' + message + '\n')
        self.file.write('sql:' + sql + '\n')

    def solution_log(self,solution):
        self.file.write('solution:' + solution + '\n')

    def __del__(self):
        self.file.close()


# 获取数据库配置
def get_config(file_path):
    config_list = []
    config = {}
    with open(file_path,encoding='utf-8') as file:
         line=file.readline()
         while(line):
            config_list.append(line.rstrip())
            line=file.readline()
    for line in config_list:
        name = line.split('=')[0]
        value = line.split('=')[1]
        if name == 'port':
            value = int(value)
        config[name] = value
    return config

def get_create_sql(file_path):
    with open(file_path,encoding='utf-8') as file:
        return file.read()
