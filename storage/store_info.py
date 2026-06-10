import json
def store_info(path,info):
    with open(path, "w") as f:
        json.dump(info, f)