import zlib
from uuid import uuid4
import os
import json
import xmltodict

BLOCK_SIZE = 510  # The max length of an episode
BLOCK_SIZE_PADDED = 509
BLOCK_MIN = 10  # The min length of an episode
cost_function = {"method": 1, "class": 0, "interface": 0, "new_line": 2}


def split_document_into_blocks_unix_padded(text, tokenizer, class_list, interface_list, method_list, max_length=2048, cnt=0, properties=None):
    ret = []
    end_tokens = get_cost_array(text, class_list, interface_list, method_list)
    poses = []
    sen_cost, break_cost = 4, 8
    for item in end_tokens:
        target_text = "\n".join(text.split("\n")[:item[0] + 1])
        tokenized_text = tokenizer.tokenize(target_text, truncation=True, max_length=max_length)
        poses.append((len(tokenized_text), item[1]))
        if len(tokenized_text) >= max_length:
            break
    text = tokenizer.tokenize(target_text, truncation=True, max_length=max_length)
    poses.insert(0, (-1, 0))
    if poses[-1][0] < len(text) - 1:
        poses.append((len(text) - 1, 0))
    x = 0
    while x < len(poses) - 1:
        if poses[x + 1][0] - poses[x][0] > BLOCK_SIZE_PADDED:
            poses.insert(x + 1, (poses[x][0] + BLOCK_SIZE_PADDED, break_cost))
        x += 1
    # simple dynamic programming
    best = [(0, 0)]
    for i, (p, cost) in enumerate(poses):
        if i == 0:
            continue
        best.append((-1, 100000))
        for j in range(i - 1, -1, -1):
            if p - poses[j][0] > BLOCK_SIZE_PADDED:
                break
            value = best[j][1] + cost + sen_cost
            if value < best[i][1]:
                best[i] = (j, value)
        assert best[i][0] >= 0
    intervals, x = [], len(poses) - 1
    while x > 0:
        l = poses[best[x][0]][0]
        intervals.append((l + 1, poses[x][0] + 1))
        x = best[x][0]
    if properties is None:
        properties = []
    for st, en in reversed(intervals):
        # copy from hard version
        cnt += 1
        tmp = text[st: en] + [tokenizer.sep_token]
        # inject properties into blks
        tmp_kwargs = {}
        for p in properties:
            if len(p) == 2:
                tmp_kwargs[p[0]] = p[1]
            elif len(p) == 3:
                if st <= p[1] < en:
                    tmp_kwargs[p[0]] = (p[1] - st, p[2])
            else:
                raise ValueError('Invalid property {}'.format(p))
        if len(tmp) > 509:
            excess = len(tmp) - 509 + 1
            tmp = tmp[:excess] + [tmp[-1]]
        pad = [tokenizer.pad_token]*(512 - len(tmp)-3)
        ret.append(tokenizer.convert_tokens_to_ids([tokenizer.cls_token, "<encoder-only>", tokenizer.sep_token] + tmp[:-1] + pad + [tmp[-1]]))

    return ret, cnt
def split_document_into_blocks_unix(text, tokenizer, class_list, interface_list, method_list, max_length=2048, cnt=0, properties=None):
    ret = []
    end_tokens = get_cost_array(text, class_list, interface_list, method_list)
    poses = []
    sen_cost, break_cost = 4, 8
    for item in end_tokens:
        target_text = "\n".join(text.split("\n")[:item[0] + 1])
        tokenized_text = tokenizer.tokenize(target_text, truncation=True, max_length=max_length)
        poses.append((len(tokenized_text), item[1]))
        if len(tokenized_text) >= max_length:
            break
    text = tokenizer.tokenize(target_text, truncation=True, max_length=max_length)
    poses.insert(0, (-1, 0))
    if poses[-1][0] < len(text) - 1:
        poses.append((len(text) - 1, 0))
    x = 0
    while x < len(poses) - 1:
        if poses[x + 1][0] - poses[x][0] > BLOCK_SIZE:
            poses.insert(x + 1, (poses[x][0] + BLOCK_SIZE, break_cost))
        x += 1
    # simple dynamic programming
    best = [(0, 0)]
    for i, (p, cost) in enumerate(poses):
        if i == 0:
            continue
        best.append((-1, 100000))
        for j in range(i - 1, -1, -1):
            if p - poses[j][0] > BLOCK_SIZE:
                break
            value = best[j][1] + cost + sen_cost
            if value < best[i][1]:
                best[i] = (j, value)
        assert best[i][0] >= 0
    intervals, x = [], len(poses) - 1
    while x > 0:
        l = poses[best[x][0]][0]
        intervals.append((l + 1, poses[x][0] + 1))
        x = best[x][0]
    if properties is None:
        properties = []
    for st, en in reversed(intervals):
        # copy from hard version
        cnt += 1
        tmp = text[st: en] + [tokenizer.sep_token]
        # inject properties into blks
        tmp_kwargs = {}
        for p in properties:
            if len(p) == 2:
                tmp_kwargs[p[0]] = p[1]
            elif len(p) == 3:
                if st <= p[1] < en:
                    tmp_kwargs[p[0]] = (p[1] - st, p[2])
            else:
                raise ValueError('Invalid property {}'.format(p))
        ret.append(tokenizer.convert_tokens_to_ids([tokenizer.cls_token, "<encoder-only>", tokenizer.sep_token] + tmp))

    return ret, cnt

def split_document_into_blocks(text, tokenizer, class_list, interface_list, method_list, max_length=2048, cnt=0, properties=None):
    ret = []
    end_tokens = get_cost_array(text, class_list, interface_list, method_list)
    poses = []
    sen_cost, break_cost = 4, 8
    for item in end_tokens:
        target_text = "\n".join(text.split("\n")[:item[0] + 1])
        tokenized_text = tokenizer.tokenize(target_text, truncation=True,  max_length=max_length)
        poses.append((len(tokenized_text), item[1]))
        if len(tokenized_text) >= max_length:
            break
    text = tokenizer.tokenize(text, truncation=True,  max_length=max_length)
    poses.insert(0, (-1, 0))
    if poses[-1][0] < len(text) - 1:
        poses.append((len(text) - 1, 0))
    x = 0
    while x < len(poses) - 1:
        if poses[x + 1][0] - poses[x][0] > BLOCK_SIZE:
            poses.insert(x + 1, (poses[x][0] + BLOCK_SIZE, break_cost))
        x += 1
    # simple dynamic programming
    best = [(0, 0)]
    for i, (p, cost) in enumerate(poses):
        if i == 0:
            continue
        best.append((-1, 100000))
        for j in range(i - 1, -1, -1):
            if p - poses[j][0] > BLOCK_SIZE:
                break
            value = best[j][1] + cost + sen_cost
            if value < best[i][1]:
                best[i] = (j, value)
        assert best[i][0] >= 0
    intervals, x = [], len(poses) - 1
    while x > 0:
        l = poses[best[x][0]][0]
        intervals.append((l + 1, poses[x][0] + 1))
        x = best[x][0]
    if properties is None:
        properties = []
    for st, en in reversed(intervals):
        # copy from hard version
        cnt += 1
        tmp = text[st: en] + [tokenizer.sep_token]
        # inject properties into blks
        tmp_kwargs = {}
        for p in properties:
            if len(p) == 2:
                tmp_kwargs[p[0]] = p[1]
            elif len(p) == 3:
                if st <= p[1] < en:
                    tmp_kwargs[p[0]] = (p[1] - st, p[2])
            else:
                raise ValueError('Invalid property {}'.format(p))
        ret.append(tokenizer.convert_tokens_to_ids(["<s>"] + tmp))

    return ret, cnt


def get_cost_array(text, class_list, interface_list, method_list):
    line_list = [item + 1 for item in range(len(text.split("\n")))]
    temp = sorted(class_list + interface_list + method_list + line_list)
    array = []
    for item in temp:
        if item in class_list:
            array.append((item, cost_function['class']))
        elif item in interface_list:
            array.append((item, cost_function['interface']))
        elif item in method_list:
            array.append((item, cost_function['method']))
        elif item in line_list:
            array.append((item, cost_function['new_line']))
    return array


def get_all_interface_name(file_name):
    interface_name_list = set()
    try:
        os.system("srcml --xpath \"//src:interface/src:name\" {}.xml >> {}_in_name.xml".format(file_name, file_name))
        json_data = convert_to_json("{}_in_name.xml".format(file_name))
        if 'unit' in json_data.keys() and 'unit' in json_data['unit'].keys():
            content = json_data['unit']['unit'] if isinstance(json_data['unit']['unit'], list) else [
                json_data['unit']['unit']]
            for item in content:
                if 'name' in item.keys() and '#text' in item['name'].keys():
                    interface_name_list.add(item['name']['#text'])
    except Exception as ex:
        print(ex)
    return list(interface_name_list)


def get_all_class_name(file_name):
    class_name_list = set()
    try:
        os.system("srcml --xpath \"//src:class/src:name\" {}.xml >> {}_cl_name.xml".format(file_name, file_name))
        json_data = convert_to_json("{}_cl_name.xml".format(file_name))
        if 'unit' in json_data.keys() and 'unit' in json_data['unit'].keys():
            content = json_data['unit']['unit'] if isinstance(json_data['unit']['unit'], list) else [
                json_data['unit']['unit']]
            for item in content:
                if 'name' in item.keys() and '#text' in item['name'].keys():
                    class_name_list.add(item['name']['#text'])
    except Exception as ex:
        print(ex)
    return list(class_name_list)


def get_all_function_name(file_name):
    function_name_list = set()
    try:
        os.system("srcml --xpath \"//src:function/src:name\" {}.xml >> {}_fn_name.xml".format(file_name, file_name))
        json_data = convert_to_json("{}_fn_name.xml".format(file_name))
        if 'unit' in json_data.keys() and 'unit' in json_data['unit'].keys():
            content = json_data['unit']['unit'] if isinstance(json_data['unit']['unit'], list) else [
                json_data['unit']['unit']]
            for item in content:
                if 'name' in item.keys() and '#text' in item['name'].keys():
                    function_name_list.add(item['name']['#text'])
    except Exception as ex:
        print(ex)
    return list(function_name_list)


def get_all_interface_position(file_name):
    interface_position_list = []
    try:
        os.system("srcml --xpath \"//src:interface\" {}.xml >> {}_in_name.xml".format(file_name, file_name))
        json_data = convert_to_json("{}_in_name.xml".format(file_name))
        if 'unit' in json_data.keys() and 'unit' in json_data['unit'].keys():
            content = json_data['unit']['unit'] if isinstance(json_data['unit']['unit'], list) else [
                json_data['unit']['unit']]
            for item in content:
                if 'interface' in item.keys() and '@pos:start' in item['interface'].keys():
                    start = int(item['interface']['@pos:start'].split(":")[0])
                    end = int(item['interface']['@pos:end'].split(":")[0])
                    if start != end:
                        interface_position_list.append(end)
    except Exception as ex:
        print(ex)
    return interface_position_list


def get_all_class_position(file_name):
    class_position_list = []
    try:
        os.system("srcml --xpath \"//src:class\" {}.xml >> {}_cl_name.xml".format(file_name, file_name))
        json_data = convert_to_json("{}_cl_name.xml".format(file_name))
        if 'unit' in json_data.keys() and 'unit' in json_data['unit'].keys():
            content = json_data['unit']['unit'] if isinstance(json_data['unit']['unit'], list) else [
                json_data['unit']['unit']]
            for item in content:
                if 'class' in item.keys() and '@pos:start' in item['class'].keys():
                    start = int(item['class']['@pos:start'].split(":")[0])
                    end = int(item['class']['@pos:end'].split(":")[0])
                    if start != end:
                        class_position_list.append(end)
    except Exception as ex:
        print("exception" + ex)
    return class_position_list


def get_all_function_position(file_name):
    function_position_list = []
    try:
        os.system("srcml --xpath \"//src:function\" {}.xml >> {}_fn_name.xml".format(file_name, file_name))
        json_data = convert_to_json("{}_fn_name.xml".format(file_name))
        if 'unit' in json_data.keys() and 'unit' in json_data['unit'].keys():
            content = json_data['unit']['unit'] if isinstance(json_data['unit']['unit'], list) else [
                json_data['unit']['unit']]
            for item in content:
                if 'function' in item.keys() and '@pos:start' in item['function'].keys():
                    start = int(item['function']['@pos:start'].split(":")[0])
                    end = int(item['function']['@pos:end'].split(":")[0])
                    if start != end:
                        function_position_list.append(end)
    except Exception as ex:
        print(ex)
    return function_position_list


def convert_to_json(file_name):
    with open(file_name, "r") as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
    delete_file(file_name)
    return data_dict


def delete_file(file_name):
    os.remove(file_name)


def parse_tree(file_data):
    try:
        file_name = str(uuid4())
        with open(file_name + ".java", "w") as file:
            file.write(file_data)
        os.system("srcml {}.java --position -o {}.xml".format(file_name, file_name))
        return file_name
    except Exception as ex:
        return None


def get_unique_bug_id(file):
    content = file.read()
    file.close()
    data = json.loads(content)
    temp = set()
    for item in data:
        temp.add(item['unique_bug_id'])
    return list(temp)


def decode(text):
    return zlib.decompress(bytes.fromhex(text)).decode().encode('utf-8').decode('utf-8')


if __name__ == "__main__":
    print(get_all_interface_position("1a2a49c0-ea83-4644-8ed1-e55fdb6fb15b"))
