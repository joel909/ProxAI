import os
def store_api_key(api_key,key_name):
    os.environ[key_name] = api_key

