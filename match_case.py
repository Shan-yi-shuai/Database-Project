import json
import sys
import difflib
from pjconfig import config
from database_api import *
from match.simth_waterman import CalculateSequeceSimilarity

database = Database(config["database"])
project_name = config["sonar_project_name"]

version_id = int(sys.argv[1])

def calc_similarity(o_iss, n_iss):
    if o_iss["type_id"] != n_iss["type_id"]:
        return 0
    code_sim = difflib.SequenceMatcher(None, o_iss["code"], n_iss["code"]).quick_ratio()
    pos_sim = CalculateSequeceSimilarity(o_iss["records"], n_iss["records"]).Answer()
    stack_sim = CalculateSequeceSimilarity(o_iss["include_records"], n_iss["include_records"]).Answer()
    return code_sim * 0.3 + pos_sim * 0.2 + stack_sim * 0.5

def match_case_in_file(path_origin, path_new = None):
    if path_new == None:
        path_new = path_origin
    iss_inst_origin_list = database.select_issue_instance(["version_id", "file_path"], [version_id - 1, project_name + ":" + path_origin])
    iss_traits_origin_dict = dict()
    for iss in iss_inst_origin_list:
        id = iss["instance_id"]
        traits = dict()
        traits["type_id"] = iss["type_id"]
        traits["case_id"] = iss["case_id"]
        traits["code"] = ""
        traits["records"] = []
        traits["include_records"] = []
        locations = database.select_issue_location(["instance_id"], [id])
        for loc in locations:
            traits["code"] += loc["code"]
            traits["records"] = loc["records"].split(',')
            traits["include_records"].extend(loc["include_records"].split(','))
        iss_traits_origin_dict[id] = traits
    # print("o dict len:", len(iss_traits_origin_dict) , iss_traits_origin_dict)
    
    iss_inst_new_list = database.select_issue_instance(["version_id", "file_path"], [version_id, project_name + ":" + path_new])
    iss_traits_new_dict = dict()
    for iss in iss_inst_new_list:
        id = iss["instance_id"]
        traits = dict()
        traits["type_id"] = iss["type_id"]
        traits["iss"] = iss
        traits["code"] = ""
        traits["records"] = []
        traits["include_records"] = []
        locations = database.select_issue_location(["instance_id"], [id])
        for loc in locations:
            traits["code"] += loc["code"]
            traits["records"] = loc["records"].split(',')
            traits["include_records"].extend(loc["include_records"].split(','))
        iss_traits_new_dict[id] = traits
    # print("n dict len:", len(iss_traits_new_dict) , iss_traits_new_dict)

    high_similarity_list = []
    for o_id, o_iss in iss_traits_origin_dict.items():
        for n_id, n_iss in iss_traits_new_dict.items():
            similarity = calc_similarity(o_iss, n_iss)
            if similarity > 0.8:
                high_similarity_list.append((similarity, o_id, n_id))
    high_similarity_list.sort(key=lambda x:x[0], reverse=True)
    for sim, o_id, n_id in high_similarity_list:
        if o_id in iss_traits_origin_dict and n_id in iss_traits_new_dict:
            database.match_issue_case(o_id, n_id)
            del iss_traits_origin_dict[o_id]
            del iss_traits_new_dict[n_id]
    for o_id, o_iss in iss_traits_origin_dict.items():
        database.close_issue_case(o_iss["case_id"], version_id)
    for n_id, n_iss in iss_traits_new_dict.items():
        case_id = database.insert_issue_case(n_iss["iss"])
        database.update_issue_instance_case(n_id, case_id)
    return

if version_id == 1:
    iss_inst_list = database.select_issue_instance(["version_id"], [version_id])
    for iss_inst in iss_inst_list:
        case_id = database.insert_issue_case(iss_inst)
        database.update_issue_instance_case(iss_inst["instance_id"], case_id)
else:
    with open('changed_files.txt', 'r') as f:
        changed_files = json.load(f)
    if "add" in changed_files:
        for path in changed_files["add"]:
            iss_inst_list = database.select_issue_instance(["version_id", "file_path"], [version_id, project_name + ":" + path])
            for iss_inst in iss_inst_list:
                case_id = database.insert_issue_case(iss_inst)
                database.update_issue_instance_case(iss_inst["instance_id"], case_id)
    if "delete" in changed_files:
        for path in changed_files["delete"]:
            iss_inst_list = database.select_issue_instance(["version_id", "file_path"], [version_id - 1, project_name + ":" + path])
            for iss_inst in iss_inst_list:
                database.close_issue_case(iss_inst["case_id"], version_id)
    if "modify" in changed_files:
        for path in changed_files["modify"]:
            match_case_in_file(path)
    if "rename" in changed_files:
        for paths in changed_files["rename"]:
            match_case_in_file(paths[1], paths[0])