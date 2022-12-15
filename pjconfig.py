import json

config = None
try:
    with open('config.json') as fp:
        config = json.load(fp)
except:
    print("config reading error!")
    exit()