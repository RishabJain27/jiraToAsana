from flask import Flask
from flask import request
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
import asana
from asana.rest import ApiException
import time
import json


app = Flask(__name__)

#Asana API configurations
configuration = asana.Configuration()
configuration.access_token = '2/1206848302395917/1206874990632238:b503b349b4150c8f73c0b5c01d1ec69c'
api_client = asana.ApiClient(configuration)
tasks_api_instance = asana.TasksApi(api_client)
sections_api_instance = asana.SectionsApi(api_client)
stories_api_instance = asana.StoriesApi(api_client)

#Jira API configurations
jira_url = "https://442561275-team-mcpys4njze6e.atlassian.net/rest/api/3/"
auth = HTTPBasicAuth("alan-phnx@442561275.asanatest1.us", "ATATT3xFfGF0LB6vcgxkYc_5u1282SmDYu3ADKUE5SaeiJbab7dflLsutr0fP7KGyc3_oEoc1zgSHxNBlCqHihoM5D3fnWk_h5fittSlipUCRdejnOJNfe2am5bK9vs3AySRu2I6x_WKjwHubub2f5Bik9OnsklsYyJc7hDRAdeU9bmFyN63Nts=4CA43465")
headers = {
    "Accept": "application/json"
}
        
def createComments(taskId, comment):
    body = {"data":{"text": comment}}
    try:
        #Create a story on a task
        stories_api_instance.create_story_for_task(body, taskId, {})
    except ApiException as e:
        pprint("Exception when calling StoriesApi->create_story_for_task: %s\n" % e)

def handleChangeTitle(currentTaskId, prevTitle, newTitle):
    updateTask(currentTaskId, {"name" : newTitle})
    
    commentStr = "From Jira: Changed the Task Name from " + prevTitle + " to " + newTitle
    createComments(currentTaskId, commentStr)

def handleChangePriority(currentTaskId, prevPriority, newPriority):
    priorityMap = {"High" : "1206874810766684", "Medium" : "1206874810766685", "Low" : "1206874810766686", "Lowest" : "1206874810766687", "Highest" : "1206874810766688"}
    updateTask(currentTaskId, {"custom_fields": {"1206874810766683" : priorityMap.get(newPriority)}})
    
    commentStr = "From Jira changed the priority from " + prevPriority + " to " + newPriority
    createComments(currentTaskId, commentStr)
    
def handleChangeDueDate(currentTaskId, prevDate, newDate):
    updateTask(currentTaskId, {"due_on" : newDate})
    
    # Format Date String to remove extra 0s and None value
    if prevDate is None or prevDate == '':
        prevDate = 'No Due Date'
    else:
        prevDate = prevDate[:-11]
    
    if newDate is None or newDate == '':
        newDate = 'No Due Date'
    else:
        newDate = newDate[:-11]
    
    #Create Comment for new date
    commentStr = "From Jira: Changed the Due Date from " + prevDate + " to " + newDate
    createComments(currentTaskId, commentStr)

def handleChangeDescription(currentTaskId, prevDescription, newDescription):
    updateTask(currentTaskId, {"notes" : newDescription})
    
    commentStr = "From Jira: Updated the Description"
    createComments(currentTaskId, commentStr)    
    
def handleChangeAssignee(currentTaskId, prevAssignee, newAssignee):
    userNameToIdMap = {"Alan PHNX" : "1206848302395917"}
    
    newAssigneeId = userNameToIdMap.get(newAssignee)
    updateTask(currentTaskId, {"assignee" : newAssigneeId})
    
    if prevAssignee is None or prevAssignee == '':
        prevAssignee = 'No Assignee'
        
    if newAssignee is None or newAssignee == '':
        newAssignee = 'No Assignee'
    
    commentStr = "From Jira: Changed Assignee from " + prevAssignee + " to " + newAssignee
    createComments(currentTaskId, commentStr)
    
def handleChangeTaskStatus(currentTaskId, prevStatus, newStatus):
    if currentTaskId == '' or currentTaskId is None:
        return
    if prevStatus == newStatus:
        return
    statusMap = {"To Do" : "1206848572644093", "In Progress" : "1206848307772957", "Ready for Launch" : "1206848572627398", "Launched": "1206884642739990"}
    section_gid = statusMap.get(newStatus)
    
    opts = {'body': {"data": {"task": currentTaskId}}}    
    try:
        # Add task to correct section
        sections_api_instance.add_task_for_section(section_gid, opts)
    except ApiException as e:
        pprint("Exception when calling SectionsApi->add_task_for_section: %s\n" % e)
    
    # Handle Change in Status to update Completion State
    prevCompleted = True if prevStatus == "Launched" else False
    newCompleted =  True if newStatus == "Launched" else False
    if prevCompleted != newCompleted:
        data = {"completed" : newCompleted}
        updateTask(currentTaskId, data)

    commentStr = "From Jira: Changed Task Status from " + prevStatus + " to " + newStatus
    createComments(currentTaskId, commentStr)

def deleteTaskById(task_gid):
    try:
        # Delete a task
        tasks_api_instance.delete_task(task_gid)
    except ApiException as e:
        print("Exception when calling TasksApi->delete_task: %s\n" % e)    

def updateTask(taskId, data):
    body = {"data": data}
    opts = {}
    
    try:
        # Update a task
        tasks_api_instance.update_task(body, taskId, opts)
    except ApiException as e:
        pprint("Exception when calling TasksApi->update_task: %s\n" % e)        

def getTaskIdByJiraId(jiraId, retry):
    while retry >= 0:
        tasks = getWebProductionTasks()
        for task in tasks:
            jiraValue = getJiraIdFromTask(task['gid'])
            if jiraValue == jiraId:
                return task['gid']
        retry = retry - 1
        if retry >= 0:
            time.sleep(2)
    return ''

def getTaskFromId(gid):
    try:
        # Get a task
        taskData = tasks_api_instance.get_task(gid, {})
        return taskData
    except ApiException as e:
        pprint("Exception when calling TasksApi->get_task: %s\n" % e)
        return None

def getJiraIdFromTask(gid):
    taskData = getTaskFromId(gid)
    if taskData is None:
        return
    
    for field in taskData['custom_fields']:
        if field['name'] == 'jiraID':
            return field['display_value']
    
    return None

def getWebProductionTasks():
    work_production_gid = "1206848441607075"
    opts = {}
    
    try: 
        # Get tasks from a project
        api_response = tasks_api_instance.get_tasks_for_project(work_production_gid, opts)
        return api_response
    except ApiException as e:
        pprint("Exception when calling TasksApi->get_tasks_for_project: %s\n" % e)
    
    return []
    
def createAsanaTask(title, description, assignee, dueDate, priority, type, jiraId):    
    if type == 'Task' or type == 'Bug':
        type = 'default_task'
    elif type == 'Epic':
        type = 'milestone'
    else:
        pprint("Ignore Invalid Task Type")
        return
    
    # Format Task information
    data = {"name": title, "resource_subtype": type, "projects": ["1206848441607075"]}
    customFields = {}
    if description != '':
        data.update({"notes" : description})
        
    if assignee != '':
        data.update({"assignee" : "me"})
    
    if dueDate != '':
        data.update({"due_on" : dueDate})
    
    # Used for Priority field (Low,Medium,High, etc..)
    # 1206874810766683: id for custom priority field
    priorityMap = {"High" : "1206874810766684", "Medium" : "1206874810766685", "Low" : "1206874810766686", "Lowest" : "1206874810766687", "Highest" : "1206874810766688"}    
    customFields.update({"1206874810766683" : priorityMap.get(priority)})
    
    # Add JiraId field
    # 1206894227644145: if for jiraId field
    customFields.update({"1206894227644145" : jiraId})
    
    data.update({"custom_fields": customFields})
    
    
    try:
        # Create a task
        api_response = tasks_api_instance.create_task({"data": data}, {})
        return api_response['gid']
    except ApiException as e:
        print("Exception when calling TasksApi->create_task: %s\n" % e)

def parseJiraIssue(payload):
    title = ''
    description = ''
    assignee = ''
    dueDate = ''
    status = ''
    priority = ''
    type = ''
    
    if 'summary' in  payload and payload['summary'] != None:
        title = payload['summary']
    if 'description' in payload and payload['description'] != None:
        description = payload['description']
    if 'assignee' in payload and payload['assignee'] != None:
        assignee = payload['assignee']['displayName']
    if 'duedate' in payload and payload['duedate'] != None:
        dueDate = payload['duedate']
    if 'status' in payload and payload['status'] != None: 
        status = payload['status']['name']    
    if 'priority' in payload and payload['priority'] != None: 
        priority = payload['priority']['name']
    if 'issuetype' in payload and payload['issuetype']['name'] != None:
        type = payload['issuetype']['name']
    
    return title, description, assignee, dueDate, status, priority, type

def parseIssueCreation(request_data):
    payload = request_data['issue']['fields']
    
    title, description, assignee, dueDate, status, priority, type = parseJiraIssue(payload)
    jiraId = request_data['issue']['key']

    createAsanaTask(title, description, assignee, dueDate, priority, type, jiraId)

def parseIssueUpdate(payload):
    jiraId = payload['issue']['key']
    currentTaskId = getTaskIdByJiraId(jiraId, 3)
    
    changeLogList = [payload['issue']['fields']]
    if payload['changelog'] != None:
        changeLogList = payload['changelog']['items']
    
    for change in changeLogList:
        field = change['field']
        prevString = change['fromString']
        newString = change['toString']
        if field == 'status':
            handleChangeTaskStatus(currentTaskId, prevString, newString)
        elif field == 'assignee':
            handleChangeAssignee(currentTaskId, prevString, newString)
        elif field == 'description':
            handleChangeDescription(currentTaskId, prevString, newString)
        elif field == 'duedate':
            handleChangeDueDate(currentTaskId, prevString, newString)
        elif field == 'priority':
            handleChangePriority(currentTaskId, prevString, newString)
        elif field == 'summary':
            handleChangeTitle(currentTaskId, prevString, newString)    
    
def parseIssueDeleted(payload):
    jiraId = payload['issue']['key']
    currentTaskId = getTaskIdByJiraId(jiraId, 1)
    
    deleteTaskById(currentTaskId)
    
@app.route('/jiraWebHook', methods=['POST'])
def webHookJira():
    request_data = request.get_json()
    
    webHookEvent = request_data['webhookEvent']
    match webHookEvent:
        case "jira:issue_created":
            parseIssueCreation(request_data)
        case "jira:issue_updated":
            parseIssueUpdate(request_data)
        case "jira:issue_deleted":
            parseIssueDeleted(request_data)
        case _:
            pprint("Not recognized Web Hook Event")
            
    return ''

def createAsanaTaskFromIssue(request_data, ignoreJiraList):
    payloadList = request_data['issues']
    for payloadJira in payloadList:
        payload = payloadJira['fields']
        title, description, assignee, dueDate, status, priority, type = parseJiraIssue(payload)
        jiraId = payloadJira['key']
        
        #Get String of description
        if description != '' and description is not None:
            descriptionString = ""
            descriptionContents = description['content']
            for content in descriptionContents:
                for innerContent in content['content']:
                    descriptionString += innerContent['text']
            description = descriptionString
    
        if jiraId not in ignoreJiraList:
            taskId = createAsanaTask(title, description, assignee, dueDate, priority, type, jiraId)
            handleChangeTaskStatus(taskId, "To Do", status)
            
@app.route('/syncToAsana', methods=['GET'])
def syncToAsana():
    
    # Gets All Valid Tasks From Jira
    issueRequest = jira_url + "search"
    
    #Only get Valid Task Types from Project
    query = {
        'jql': 'project = "Go to market sample" and type in (Epic, Bug, Task)'
    }
    
    response = requests.request(
        "GET",
        issueRequest,
        headers=headers,
        params=query,
        auth=auth
    )
    json_response = json.loads(response.text)
    
    #Create list of jiraId with no associated Asana Task
    listAsanaTasks = list(getWebProductionTasks())
    ignoreJiraList = []
    for asanaTask in listAsanaTasks:
        jiraValue = getJiraIdFromTask(asanaTask['gid'])
        if jiraValue != None or jiraValue != '':
            ignoreJiraList.append(jiraValue)
            
    createAsanaTaskFromIssue(json_response, ignoreJiraList)
    
    return ''    

if __name__ == "__main__":
    app.run(debug=True)

