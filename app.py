from flask import Flask
from flask import request
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
import json

app = Flask(__name__)

@app.route('/jiraWebHook', methods=['GET','POST'])
def webHook():
    pprint('HERE')
    return 'Hello World'


@app.route('/jiraProjects', methods=['GET'])
def getProjects():
    url = "https://442561275-team-mcpys4njze6e.atlassian.net/rest/api/3/project/search"

    auth = HTTPBasicAuth("alan-phnx@442561275.asanatest1.us", "ATATT3xFfGF0dEdMkTXmZ4gXrwLmIYq87EqI_BSapeR_NcLmHZGZ6-HU86lD0RmRgUzbkFAP0Ardw244vvVqG5XtPaLn_yA8ebOOWrbIUPj6A38hoylAYctjubKILRveFkwL4V1HNDLjJuBJVGAG4zuIKNm8vOBFoFOlDJ5reAEWhO4Xs47-3-M=BA3485FD")

    headers = {
        "Accept": "application/json"
    }

    response = requests.request(
    "GET",
    url,
    headers=headers,
    auth=auth
    )

    return response


if __name__ == "__main__":
    app.run(debug=True)

