import argparse
import threading
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool
import pandas as pd
import os
import subprocess
import zlib
from tqdm import tqdm
import uuid
import json
from multiprocessing.pool import ThreadPool as thread_pool

def encode(text):
    return zlib.compress(text.encode()).hex()

def task(file_path):
    if os.path.isfile(file_path):
        file = open(file_path, "rb")
        content = file.read().decode('utf-8', errors='ignore')
        file.close()
        return encode(content)
    else:
        return encode("")
def decode(text):
    return zlib.decompress(bytes.fromhex(text)).decode().encode('utf-8').decode('utf-8')
def get_final_df(df, project):
    rows_list = []
    df = df[df['project_name'] == project].sort_values(by='bug_id', ascending=False).reset_index(drop=True)

    for item in tqdm(df.iterrows(), total=df.shape[0]):
        unique_bug_id = str(uuid.uuid4())
        try:
            subprocess.check_output("git reset --hard {}".format(item[1]['before']), shell=True)
        except Exception as ex:
            print("Can't reset to version {}".format(item[1]['before']))
            continue
        file_list = [os.path.join(dp, f)[2:] for dp, dn, filenames in os.walk(".") for f in filenames if os.path.splitext(f)[1] == '.java']
        file_list = list(filter(lambda x: "test" not in x, file_list))
        output = subprocess.check_output("git diff --name-only {} {}".format(item[1]['before'], item[1]['after']), shell=True)
        updated_file_list = [item for item in output.decode('utf-8', errors='ignore').split("\n") if len(item) >0 and ".java" in item and "test" not in item]
        uncommon_files = set(file_list) - set(updated_file_list)
        common_files = set(file_list).intersection(set(updated_file_list))
        with thread_pool(processes=16) as pool:
            uncommon_code_data = pool.map(task, uncommon_files)
        with thread_pool(processes=16) as pool:
            common_code_data = pool.map(task, common_files)
        for path, data in zip(uncommon_files, uncommon_code_data):
            rows_list.append({
                "bug_id": item[1]['bug_id'],
                'summary': item[1]['title'],
                'description': item[1]['description'],
                'report_time': None,
                "report_timestamp": None,
                "status": None,
                "commit": item[1]['after'],
                "commit_timestamp": None,
                "unique_bug_id": unique_bug_id,
                "doc_id": str(uuid.uuid4()),
                "file_content": data,
                "file_path": path,
                "match": 0



            })
        for path, data in zip(common_files, common_code_data):
            rows_list.append({
                "bug_id": item[1]['bug_id'],
                'summary': item[1]['title'],
                'description': item[1]['description'],
                'report_time': None,
                "report_timestamp": None,
                "status": None,
                "commit": item[1]['after'],
                "commit_timestamp": None,
                "unique_bug_id": unique_bug_id,
                "doc_id": str(uuid.uuid4()),
                "file_content": data,
                "file_path": path,
                "match": 1

            })
        if len(rows_list) % 10:
            final_df = pd.DataFrame(rows_list)
            final_df.to_csv("{}.csv".format(project), index=False)

    final_df = pd.DataFrame(rows_list)
    final_df.to_csv("{}.csv".format(project), index=False)
    return final_df

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # #parser.add_argument('--data_path', default="/project/def-m2nagapp/partha9/LTR/", help='Data Path')
    # parser.add_argument('--clone_path', default="/project/def-m2nagapp/partha9/LTR/", help='Clone Path')
    # parser.add_argument('--project_name', default="/project/def-m2nagapp/partha9/LTR/", help='Project Name')
    # #parser.add_argument('--start_from', default="0", help='Project Name')
    #
    # options = parser.parse_args()
    # #data_path = options.data_path
    # clone_path = options.clone_path
    # project = options.project_name
    #start_from = int(options.start_from)

    data_path = "dataset/"
    clone_path = "."
    project = "jackrabbit"
    # start_from = 0

    git_repo = {
        "httpclient": "https://github.com/apache/httpcomponents-client.git",
        "lucene-solr": "https://github.com/mdodsworth/lucene-solr.git",
        "jackrabbit": "https://git.apache.org/jackrabbit.git"

    }
    df = pd.read_csv("Combined_Data_AL.csv")
    os.chdir(clone_path)
    os.system("git clone {}".format(git_repo[project]))
    dir_name = ".".join(git_repo[project].split("/")[-1].split(".")[0:-1])
    os.chdir(dir_name)
    final_df = get_final_df(df, project=project)
    #subprocess.check_output("mv {}.csv {}/{}.csv".format(project, save_path, project), shell=True)

