import json
import seaborn as sns
from matplotlib import pyplot as plt
import pandas as pd
from transformers import AutoTokenizer
import itertools
from tqdm import tqdm
def get_token_list(file_name, tokenizer):
    tqdm.pandas()
    df = pd.read_csv(file_name)
    project_name = file_name.split("/")[1].split(".")[0]
    df['summary'] = df['summary'].fillna("")
    df['description'] = df['description'].fillna("")
    df['joined'] = df['summary'] + " " + df['description']
    tokens = df['joined'].progress_map(lambda x: tokenizer.tokenize(x) if x else "")
    token_list = list(itertools.chain(*tokens.tolist()))
    with open("Data/{}.json".format(project_name), "w") as f:
        json.dump(token_list, f)
    del df
    return token_list

def get_data():
    tokenizer = AutoTokenizer.from_pretrained("microsoft/unixcoder-base")
    get_token_list(file_name="Data/httpclient.csv", tokenizer=tokenizer)
    get_token_list(file_name="Data/lucene-solr.csv", tokenizer=tokenizer)
    get_token_list(file_name="Data/AspectJ.csv", tokenizer=tokenizer)
    get_token_list(file_name="Data/jackrabbit.csv", tokenizer=tokenizer)
    get_token_list(file_name="Data/JDT.csv", tokenizer=tokenizer)
    get_token_list(file_name="Data/SWT.csv", tokenizer=tokenizer)
    get_token_list(file_name="Data/Eclipse_Platform_UI.csv", tokenizer=tokenizer)

def get_percentage():
    names = ['httpclient', 'lucene-solr', 'AspectJ', 'jackrabbit', 'JDT', 'SWT', 'Eclipse_Platform_UI']
    result = []
    for source, target in tqdm(list(itertools.permutations(names, 2))):
        with open("Data/{}.json".format(source), "r") as fs:
            source_tokens = json.load(fs)
        with open("Data/{}.json".format(target), "r") as ft:
            target_tokens = json.load(ft)
        unique_source = set(source_tokens)
        unique_target = set(target_tokens)
        common_tokens = round((len(unique_source.intersection(unique_target)) / len(unique_target)) * 100, 4)
        result.append({
            "Source": source,
            "Target": target,
            "Common": common_tokens

        })
        print("Source: {} Target:{} Common: {}%".format(source, target, common_tokens))
        del source_tokens
        del target_tokens
    df = pd.DataFrame(result)
    df.to_csv("Common_Tokens.csv", index=False)
if __name__ == "__main__":
    names = ['httpclient', 'lucene-solr', 'AspectJ', 'jackrabbit', 'JDT', 'SWT', 'Eclipse_Platform_UI']
    drop_names = ['JDT', 'SWT', 'Eclipse_Platform_UI']
    df = pd.read_csv("Common_Tokens.csv")
    add_tuples = []
    for item in names:
        df = df.append({
            "Source": item,
            "Target": item,
            "Common": 100

        }, ignore_index=True)
    df = df.drop(df[(df['Source'].isin(drop_names)) | (df['Target'].isin(drop_names))].index)
    df.replace({
        "httpclient": "HttpClient",
        "lucene-solr": "Lucene-Solr",
        "jackrabbit": "Jackrabbit"
    }, inplace=True)
    df.sort_values(by=['Source', 'Target'],ascending=[True, True], inplace=True)
    # df.set_index("Source", inplace=True)
    df_heatmap = df.pivot_table(index='Source', columns='Target', values='Common')
    plt.rcParams["font.size"] = "20"
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df_heatmap, annot=True, cmap='YlGnBu',ax=ax)
    plt.tight_layout()
    plt.savefig('Token_Heatmap.eps', format='eps', dpi=500)
    # plt.show()
    # http_unique = set(http_tokens)
    # lucene_unique = set(lucene_tokens)
    # aspectj_unique = set(aspectj_tokens)
    #
    # print("AspectJ: Lucene {}".format(len(aspectj_unique.intersection(lucene_unique))/ len(aspectj_unique)))
    # print("AspectJ: HttpClient {}".format(len(aspectj_unique.intersection(http_unique))/ len(aspectj_unique)))
    # print("HttpClient: AspectJ {}".format(len(http_unique.intersection(aspectj_unique))/ len(http_unique)))
    # print("HttpClient: Lucene {}".format(len(http_unique.intersection(lucene_unique))/ len(http_unique)))
    # print("Lucene: AspectJ {}".format(len(lucene_unique.intersection(aspectj_unique))/ len(lucene_unique)))
    # print("Lucene: HttpClient {}".format(len(lucene_unique.intersection(http_unique))/ len(lucene_unique)))
