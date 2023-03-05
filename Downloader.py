import argparse
import wget
from pathlib import Path
import os
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None, type=str,
                        help="Project Name")
    parser.add_argument("--file", default=None, type=str,
                        help="File Name")
    args = parser.parse_args()
    BUCKET_NAME = "researchdataset"
    PROJECT_NAME = args.project
    FILE_NAME = args.file
    # BUCKET_NAME = "researchdataset"
    # PROJECT_NAME = "New_BL_Dataset"
    # FILE_NAME = "httpclient.csv"
    BASE_URL = "https://researchdatastorage.s3.amazonaws.com/New_BL_Dataset/{}"
    Path("Data/{}".format(PROJECT_NAME)).mkdir(parents=True, exist_ok=True)
    os.chdir("Data/{}".format(PROJECT_NAME))
    if FILE_NAME:
        wget.download(BASE_URL.format(PROJECT_NAME) + "/" + FILE_NAME)
    else:
        for file_name in ["{}.csv", "{}.json", "{}_ES_Search_Result.json"]:
            wget.download(BASE_URL.format(PROJECT_NAME) + "/" + file_name.format(PROJECT_NAME))