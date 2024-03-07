# This is a sample Python script.
import subprocess
from subprocess import PIPE
import json
from module import pullRequestData, commitData, projectData
import mysql.connector
import os
import time
import glob
import emoji

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
def readJson(jfile):
    Request_Data = {}
    AllProject_list = set()
    FilteredProject_list = set()
    AllPR = set()
    AllPR_number = set()
    AllLink = set()
    FilteredPR = set()
    Id = 0
    title = ''
    url = ''
    body = ''
    mentioned_url = ''
    create_time = ''
    mentioned_text_check = []

    for path in filePath:
        with open(path, 'r+') as f:
            jfile = json.load(f)

        for source in jfile['data']['search']['edges']:
            nodes = source.get('node',[])
            if source == []:
                print('edgeが入っていません')
                raise
            for node_key,node_value in nodes.items():
                if node_key == 'author':
                    author = node_value['login']
                    print(author)
                if node_key == 'createdAt':
                    create_time = node_value
                if node_key == 'body':
                    body = node_value[:1000]
                if node_key == 'title':
                    title = node_value
                    AllProject_list.add(str(title))
                if node_key == 'url':
                    url = node_value
                    AllPR.add(url)
                if node_key == 'number':
                    AllPR_number.add(node_value)

                if node_key == 'comments':
                    comments = node_value.get('nodes',[])
                    commentChatGPT = False
                    commentAuthorFlag = False
                    commentUrlFlag = False
                    for comment in comments:
                        comment_url = comment.get('url',[])
                        print(comment_url)
                        commentAuthorInfo = comment.get('author', [])
                        comment_text = comment.get('bodyText',[])
                        if not comment_url is None:
                            AllLink.add(comment_url)
                            commentUrlFlag = True


                        if not commentAuthorInfo is None:
                            commentAuthor = commentAuthorInfo['login']
                            commentAuthorFlag = True
                            print("author"+str(commentAuthor))


                        if "https://chat.openai.com/share/" in comment_text:
                            if not comment_text in mentioned_text_check:
                                print(comment_text)
                                print("--------------------------------")
                                mentioned_text_check.append(comment_text)
                                commentChatGPT = True

                        if commentChatGPT == True and commentAuthorFlag == True and commentUrlFlag == True:
                            if author != commentAuthor:
                                FilteredProject_list.add(str(title))
                                FilteredPR.add(comment_url)

                                Id += 1
                                Request_Data[Id] = pullRequestData.PullRequestData(author, body,
                                                                                   commentAuthor,
                                                                                   comment_text,
                                                                                   comment_url,
                                                                                   create_time,
                                                                                   path)


                        commentChatGPT = False
                        commentAuthorFlag = False
                        commentUrlFlag = False


                if node_key == 'reviews':
                    reviews = node_value.get('edges',[])
                    for review in reviews:
                        reviewNodes = review.get('node',[])
                        for reviewNode_key, reviewNodes_value in reviewNodes.items():
                            if reviewNode_key == 'comments':
                                reviewCommentEdges = reviewNodes_value.get('edges',[])
                                for reviewCommentEdge in reviewCommentEdges:
                                    reviewCommentNodes = reviewCommentEdge.get('node', [])
                                    chatGPT = False
                                    authorFlag = False
                                    urlFlag = False
                                    for reviewCommentNodes_key,reviewCommentNodes_value in reviewCommentNodes.items():
                                        if reviewCommentNodes_key == 'url':
                                            mentioned_url = reviewCommentNodes_value
                                            AllLink.add(mentioned_url)
                                            urlFlag = True

                                        if reviewCommentNodes_key == 'author':
                                            mentionedAuthor = reviewCommentNodes_value['login']
                                            authorFlag = True
                                        if reviewCommentNodes_key == 'bodyText':
                                            mentioned_text = reviewCommentNodes_value
                                            if "https://chat.openai.com/share/" in mentioned_text:
                                                if not mentioned_text in mentioned_text_check:
                                                    mentioned_text_check.append(mentioned_text)
                                                    chatGPT = True

                                        if chatGPT == True and authorFlag == True and urlFlag ==True:
                                            if author != mentionedAuthor:
                                                FilteredProject_list.add(str(title))
                                                FilteredPR.add(mentioned_url)

                                                Id += 1
                                                Request_Data[Id] = pullRequestData.PullRequestData(author, body,
                                                                                                   mentionedAuthor,
                                                                                                   mentioned_text,
                                                                                                   mentioned_url,
                                                                                                   create_time,
                                                                                                   path)
                                                chatGPT = False
                                                authorFlag = False
                                                urlFlag = False
                                            else:
                                                chatGPT = False
                                                authorFlag = False
                                                urlFlag = False






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
                       url VARCHAR(5000) NOT NULL COLLATE utf8mb4_unicode_ci , 
                       PRIMARY KEY (id)
                       )""")
    except Exception as e:
        print(f"Error creating table: {e}")


#
# Add data
#
def addDataBase(cursor, directory, author, reviewer, body, mention, url, create_time):
    # Add data
    sql = "INSERT INTO pullRequestTable(directory, author, createtime,reviewer, body, mention, url) VALUES(%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, (directory, author, create_time,reviewer, body, mention[:1000], url))
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
    # path = './data/day/data_2023-05-27T00:00:00_3.json'
    json_dict = readJson(filePath)
    # for path in filePath:
    #     with open(path, 'r+') as f:
    #         jfile = json.load(f)

    # pullrequestのreturnを下のfor分に追加
    print(json_dict.allCommitData.get_string())
    for value in json_dict.Request_Data.values():
        value.mention = emoji.replace_emoji(value.mention)
        value.body = emoji.replace_emoji(value.body)
        if value.url=="":
            print("error")
        addDataBase(cursor, value.path, value.writeAuthor, value.reviewAuthor, value.body, value.mention, value.url,
                        value.create_time)

    # PRs = deleteSamecommit(json_dict)
