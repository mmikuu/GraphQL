# This is a sample Python script.
import subprocess
from subprocess import PIPE
import json
from module import pullRequestData, commitData, projectData
import mysql.connector
import os
import time
import glob

#
# 　git clone
#
# work_directory = '/work/'
work_directory = os.getcwd()+"/../"
git_directory = work_directory+"DevGPT"
def run_command(command):
    print(command)
    try:
        proc = subprocess.Popen(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
        result = proc.communicate()
        #subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        print(f'Error: {e}')

# Currently the repository is down
def git_clone():
    repository_url = 'https://github.com/NAIST-SE/DevGPT.git'
    command = f'git clone --depth=1 {repository_url} {git_directory}'
    run_command(command)
    print(f'Repository cloned to {git_directory}')

def wget_repo():
    # url = "https://zenodo.org/records/10086809/files/DevGPT.zip"
    # For faster download
    url = '"https://www.dropbox.com/scl/fi/gmk78pj7wzans0xwnh54r/DevGPT.zip?rlkey=0whnsupvytss5hftvcr0kr6k0&dl=1"'
    run_command(f"wget -O {git_directory}.zip {url}")
    print(f'Repository downloaded to {work_directory}')
    import zipfile
    with zipfile.ZipFile(f"{git_directory}.zip", 'r') as zip_ref:
        zip_ref.extractall(work_directory)


#
# 　Extract data from snapshot
#
def readJson(filePath):
    Request_Data = {}
    AllProject_list = set()
    FilteredProject_list = set()
    AllPR = set()
    AllPR_number = set()
    AllLink = set()
    FilteredPR = set()
    Id = 0

    with open(filePath) as f:
        di = json.load(f)
        print(type(di))

    for source in di['data']:
        searches = source.get('search')
        for search in searches:
            edges = search.get('node',{})
            print("edge"+edges)
            if edges == []:
                return None
            for edge in edges:
                nodes = edge.get('node')
                for node in nodes:
                    author = node['author']
                    create_time = node.get('CreatedAt', [])
                    body = node.get('Body', [])[:1000]
                    AllProject_list.add(str(node.get('title', [])))
                    AllPR.add(node.get('url', []))
                    AllPR_number = node.get('number',[])
                    reviews = node.get('reviews')
                for review in reviews:
                    reviewEdges = review.get('edges')
                    for reviewEdge in reviewEdges:
                        reviewNodes = reviewEdge.get('node')
                        for reviewNode in reviewNodes:
                            mentioned_text= reviewNode.get('bodyText', [])
                            if(mentioned_text.contains("chat.openai")):
                                mentioned_url = reviewNode.get('url', [])
                                AllLink.add(mentioned_url)
                                mentionedAuthorInfo = reviewNode.get('author', [])
                                mentionedAuthor = mentionedAuthorInfo.get('login', [])

                                if author != mentionedAuthor:
                                    FilteredProject_list.add(str(node.get('title', [])))
                                    FilteredPR.add(node.get('url', []))

                                    Id += 1
                                    Request_Data[Id] = pullRequestData.PullRequestData(author, body, mentionedAuthor, mentioned_text,mentioned_url,create_time)
    print(len(AllPR_number))
    allCommitData = projectData.projectData(len(AllProject_list), len(FilteredProject_list), len(AllPR),
                                            len(FilteredPR), len(AllLink), len(Request_Data))
    pullResult = commitData.commitData(allCommitData, Request_Data)
    return pullResult


#
# create DB
#
def creatTable(cursor):
    cursor.execute("DROP TABLE IF EXISTS pullRequestTable")
    try:
        cursor.execute("""CREATE TABLE pullRequestTable(
                       id INT(11) AUTO_INCREMENT NOT NULL,
                       directory VARCHAR(1000) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       author VARCHAR(100) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       createtime VARCHAR(100) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       reviewer varchar(100) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       body VARCHAR(5000) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       mention VARCHAR(5000) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       url VARCHAR(1000) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       PRIMARY KEY (id)
                       )""")
    except Exception as e:
        print(f"Error creating table: {e}")


#
# Add data
#
def addDataBase(cursor, directory, author, reviewer, body, mention, url, create_time):
    # Add data
    sql = "INSERT INTO pr_commit_list(directory, author, createtime,reviewer, body, mention, url) VALUES(%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, (directory, author, create_time,reviewer, body, mention, url))
    connection.commit()


#
# delete same commit
#
def deleteSamecommit(json_dict):
    validator = set()
    distinct_PRs = []
    for _, pre_value in json_dict.items():
        for _, p_value in pre_value.Request_Data.items():
            if p_value.get_string() in validator:
                # print("already exist")
                pass
            else:
                distinct_PRs.append(p_value)
                validator.add(p_value.get_string())
    return distinct_PRs

def getFilePath():
    file = []
    file.extend(glob.glob("./data/day/*"))
    file.extend(glob.glob("./data/hour/*"))
    file.extend(glob.glob("./data/min/*"))
    return file

if __name__ == '__main__':
    # wget_repo() 意味がわからんかって動かんから一旦コメントアウト
    connection = mysql.connector.connect(
        host='localhost',
        user='me',
        passwd='goma',
        db='ease',
        auth_plugin='mysql_native_password')
    cursor = connection.cursor()

    creatTable(cursor)

    # fileHead = "../DevGPT/"
    # fileHead = git_directory+"/"
    filePath = getFilePath()
    print(filePath)

    json_dict = {}
    for path in filePath:
        # json_dict[path] = readJson(fileHead + path)
        json_dict[path] = readJson(path)

    for k, data in json_dict.items():
        print(data.allCommitData.get_string())
        for value in data.Request_Data.values():
            addDataBase(cursor, k, value.writeAuthor, value.reviewAuthor, value.body, value.mention, value.url,
                            value.create_time)

    PRs = deleteSamecommit(json_dict)
