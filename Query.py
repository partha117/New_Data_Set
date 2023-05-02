import json
from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
from utils import get_unique_bug_id
from pathlib import Path
import re
import os
def remove_import(text):
    regex = r"(package|import) (.|\s)*?(,|\n)"
    return re.sub(regex, " ", text, 0)
def remove_comments(text):
    regex = r"/\*\*(.|\n)*?\*/"
    return re.sub(regex, " ", text, 0)
def query_by_report(project_name, bug_id, report, return_count=10):
    client = Elasticsearch()
    s = Search(using=client)
    query = Q('bool',
              # must=[Q('match', title='python')],
              should=[Q('match', codes=report), Q('simple_query_string', query=report,
                                                  fields=["names.class_name", "names.interface_name",
                                                          "names.method_name", "file_name", "file_path"])],
              minimum_should_match=0
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name}).filter('term',
                                                                          **{"unique_bug_id.keyword": bug_id}).source(
        ['doc_id', 'bug_id', 'unique_bug_id', 'position', 'buggy'])[0:return_count]
    result = s.execute()
    return [(hit.doc_id, hit.bug_id, hit.unique_bug_id, hit.meta.score,
             hit.position if hasattr(hit, 'position') else None, hit.buggy) for hit in s]


def query_history(project_name, bug_id, report, return_count=10):
    client = Elasticsearch()
    s = Search(using=client)
    query = Q('bool',
              should=[Q("match", report=report)],
              must_not=Q('term', **{"unique_bug_id.keyword": bug_id}),
              must=Q('term', buggy=True),
              minimum_should_match=0
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name})
    s = s.source(['doc_id', 'bug_id', 'unique_bug_id', 'codes'])[0:return_count]
    s.execute()
    return [(hit.codes, hit.meta.score) for hit in s]


def query_by_code(project_name, bug_id, codes, restricted_doc, return_count=10):
    client = Elasticsearch()
    s = Search(using=client)
    #print(len(remove_import(remove_comments(codes))))
    query = Q('bool',
              should=[Q("match", codes=remove_import(remove_comments(codes))[:43263])],
              must=Q('term', **{"unique_bug_id.keyword": bug_id}),
              must_not=Q('terms', doc_id=restricted_doc),
              minimum_should_match=0
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name})
    s = s.source(['doc_id', 'bug_id', 'unique_bug_id', 'position', 'buggy'])[0:return_count]
    s.execute()
    return [(hit.doc_id, hit.bug_id, hit.unique_bug_id, hit.meta.score,
             hit.position if hasattr(hit, 'position') else None, hit.buggy) for hit in s]


def query_buggy(mode, project_name, bug_id):
    client = Elasticsearch()
    s = Search(using=client)
    query = Q('bool',
              must=[Q('term', **{"unique_bug_id.keyword": bug_id}), Q('term', buggy=True)]
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name})
    s = s.source(['doc_id'])
    s.execute()
    return [hit.doc_id for hit in s]


def query_distinct_bugs(mode, project_name, return_count=500):
    client = Elasticsearch()
    s = Search(using=client)
    bug_count = A("terms", field="bug_id", size=return_count)
    s.aggs.bucket("bug_count", bug_count)
    s = s.filter('term', mode=mode).filter('term', project_name=project_name)
    s = s.source(['report', 'unique_bug_id'])[0:return_count]
    response = s.execute()
    return [(tag.bug_id, tag.report) for tag in response.hits]




def get_random(project_name):
    client = Elasticsearch()
    s = Search(using=client)
    query = Q('bool'
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name})
    response = s.execute()
    return response.hits


def get_all_positions(project_name):
    client = Elasticsearch(timeout=50, max_retries=10, retry_on_timeout=True)
    s = Search(using=client)
    query = Q('bool'
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name})
    total = s.count()
    s = s.source(['doc_id', 'unique_bug_id', 'position'])[0: total]
    s = s.params(preserve_order=False)
    response = s.scan()
    return [item.to_dict() for item in response]


def get_report(project_name, bug_id):
    client = Elasticsearch()
    s = Search(using=client)
    query = Q('bool',
              must=[Q('term', **{"unique_bug_id.keyword": bug_id})]
              )
    s.query = query
    s = s.filter('term', **{"project_name.keyword": project_name})
    s = s.source(['report'])[0:2]
    response = s.execute()
    return response.hits[0].report


def create_query_data(project_name, bug_id, report, return_count=100, per_history_match=10):
    from_report = round(return_count * 0.95)
    from_history = round(return_count * 0.05)
    results = query_by_report(project_name=project_name, bug_id=bug_id, report=report,
                              return_count=from_report)
    history_results = query_history(project_name=project_name, bug_id=bug_id, report=report,
                                    return_count=round(from_history / per_history_match))
    restricted_doc = [item[0] for item in results]
    for doc in history_results:
        temp = query_by_code(project_name=project_name, bug_id=bug_id, codes=doc[0],
                             restricted_doc=restricted_doc, return_count=per_history_match)
        results.extend(temp)
        for item in temp:
            restricted_doc.append(item[0])
    return results


def search_for(project_name):
    file = open("{}/{}.json".format(project_name, project_name), "r")
    new_file = open("{}/{}.json".format(project_name, project_name), "r")
    random_data = get_unique_bug_id(file)
    new_random_data = get_unique_bug_id(new_file)
    random_data = random_data + new_random_data
    data = dict()
    for bug_id in tqdm(random_data):
        report = get_report(project_name, bug_id)
        report = report[0:6000]
        all_results = create_query_data(project_name=project_name, bug_id=bug_id,
                                        report=report,
                                        per_history_match=13, return_count=50)

        unzipped_results = list(zip(*all_results))
        data[bug_id] = {"doc_id": unzipped_results[0], "bug_id": unzipped_results[1], "score": unzipped_results[3],
                        "match": unzipped_results[5]}

    Path("{}/".format(project_name)).mkdir(parents=True, exist_ok=True)
    with open("{}/{}_ES_Search_Result.json".format(project_name, project_name), "w") as file:
        json.dump(data, file)


if __name__ == "__main__":
    project_name = "lucene-solr"
    search_for(project_name=project_name)

