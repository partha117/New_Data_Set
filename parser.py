import json
import os
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from utils import decode, parse_tree, get_all_class_name, get_all_function_name, delete_file, get_all_interface_name, get_all_function_position, get_all_class_position, get_all_interface_position
import threading
import json
from multiprocessing import cpu_count
def processor(row, position_and_name_required):
    file_content = decode(row[1].file_content)
    if position_and_name_required:
        file_name = parse_tree(file_content)
        if file_name is not None:
            functions_list = get_all_function_name(file_name)
            function_position = get_all_function_position(file_name)
            class_position = get_all_class_position(file_name)
            interface_position = get_all_interface_position(file_name)
            class_list = get_all_class_name(file_name)
            interface_list = get_all_interface_name(file_name)
            delete_file("{}.xml".format(file_name))
            delete_file("{}.java".format(file_name))
        else:
            functions_list, class_list, interface_list, function_position, class_position, interface_position = [], [], [], [], [], []
    else:
        functions_list, class_list, interface_list, function_position, class_position, interface_position = [], [], [], [], [], []

    return {
            "id": row[1].bug_id,
            "unique_bug_id": row[1].unique_bug_id,
            "doc_uuid": row[1].doc_id,
            "contents": file_content,
            "report": row[1]['summary'].encode('utf-8').decode('utf-8') if row[1]['summary'] is not None else "" + " " + row[1].description.encode('utf-8').decode('utf-8') if row[1].description is not None else "",
            "buggy": True if row[1]['match'] == 1 else False,
            "report_timestamp": row[1]['report_timestamp'],
            "file_path": row[1]['file_path'],
            "position": {
                "class": class_position,
                "interface": interface_position,
                "Method": function_position
            },
            "NER": {
                "Class_Name": class_list,
                'Method_Name': functions_list,
                "Interface_Name": interface_list
            }
        }


def handle_json_data(file_content):
    file_name = parse_tree(file_content)
    if file_name is not None:
        functions_list = get_all_function_name(file_name)
        function_position = get_all_function_position(file_name)
        class_position = get_all_class_position(file_name)
        interface_position = get_all_interface_position(file_name)
        class_list = get_all_class_name(file_name)
        interface_list = get_all_interface_name(file_name)
        delete_file("{}.xml".format(file_name))
        delete_file("{}.java".format(file_name))
    else:
        functions_list, class_list, interface_list, function_position, class_position, interface_position = [], [], [], [], [], []
    return {"position": {
                "class": class_position,
                "interface": interface_position,
                "Method": function_position
            },
            "NER": {
                "Class_Name": class_list,
                'Method_Name': functions_list,
                "Interface_Name": interface_list
            },
        "contents": file_content
    }
def convert_to_json(project_name, train=False):
    # id same means they are from the same bug report
    full_path = "../Data/Json_Data/" + ("Train/" if train else "Test/") + project_name + "/"
    Path(full_path).mkdir(parents=True, exist_ok=True)
    full_path += project_name + ".json"
    if train:
        data_path = "../Data/" + "TrainData/" + "Bench_BLDS_" + project_name + "_Dataset.csv"
    else:
        data_path = "../Data/" + "TestData/" + project_name + "_test.csv"
    df = pd.read_csv(data_path)
    if not train:
        df = df.drop(
            columns=["summary", "description", "report_time", "report_timestamp", "status", "commit",
                     "commit_timestamp", "files", "Unnamed: 10", "bug_recency", "report_id", "rVSM_similarity",
                     "bug_frequency", "classname_similarity", "file", "collab_filter"], axis=1)
    with ThreadPoolExecutor(max_workers=8) as executor:
        lock = threading.Lock()
        data_list = []
        futures = set()
        for row in tqdm(df.iterrows(), total=df.shape[0]):
            if len(futures) >= 8:
                completed, futures = wait(futures, return_when=FIRST_COMPLETED)
            args = {
                "row": row,
                "data_list": data_list,
                "lock": lock
            }
            futures.add(executor.submit(processor, **args))
            # processor(row=row, data_list=data_list, lock=lock)
    with open(full_path, "w") as file:
        print("Dumping into file")
        json.dump(data_list, file)

def convert_full_data(project_name,position_and_name_required):
    df = pd.read_csv("{}/{}.csv".format(project_name, project_name))
    if os.path.isfile("{}.json".format(project_name)):
        with open("{}.json".format(project_name), "r") as f:
            data_list = json.load(f)
            id_list = [item['unique_bug_id'] for item in data_list]
    else:
        data_list = []
        id_list = []
    with ThreadPoolExecutor(max_workers=cpu_count() * 2 - 1) as executor:
        for bug_id in tqdm(df['unique_bug_id'].unique().tolist()):
            if bug_id not in id_list:
                id_list.append(bug_id)
                temp_df = df[df['unique_bug_id'] == bug_id]
                processes = []
                for row in temp_df.iterrows():
                    args = {
                        "row": row,
                        "position_and_name_required": position_and_name_required
                    }
                    processes.append(executor.submit(processor, **args))
                for _ in concurrent.futures.as_completed(processes):
                    data_list.append(_.result())

                if len(data_list) % 10 == 0:
                    with open("{}.json".format(project_name), "w") as f:
                        json.dump(data_list, f)
    with open("{}.json".format(project_name), "w") as f:
        json.dump(data_list, f)
if __name__ == "__main__":
    convert_full_data(project_name='jackrabbit', position_and_name_required=True)

