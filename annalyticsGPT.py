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

from module.pullRequestData import Comment, PullRequestData

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
def extract_comment(node):
    c = Comment()
    c.url = node.get('url')
    c.comment_text = node.get('bodyText', [])
    if "https://chat.openai.com/share/" in c.comment_text:
        c.has_chatGPT_link = True
    if not node.get('author', []) is None:
        c.author = node.get('author', [])['login']
    if not node.get('originalCommit') is None:
        c.date = node.get('originalCommit')['authoredDate']  # TODO: should be commented date
    return c
def extract_comments(node_value):
    comments = []
    if node_value is None:
        return comments
    nodes = node_value.get('nodes', [])
    for node in nodes:
        comments.append(extract_comment(node))
    return comments

def extract_review_comments(node_value):
    comments = []
    edges = node_value.get('node', []).get("comments",[]).get("edges",[])
    for edge in edges:
        node = edge.get("node")
        comments.append(extract_comment(node))
    return comments


def extract_reviews(node_value):
    all_comments = []
    reviews = node_value.get('edges', [])
    for review in reviews:
        comments = extract_review_comments(review)
        all_comments.extend(comments)
    return all_comments





def extract(jfile):
    pull_requests = []
    for source in jfile['data']['search']['edges']:
        pr = pullRequestData.PullRequestData()
        nodes = source.get('node', [])
        if source == []:
            print('no edge')
            raise
        pr.author = nodes.get('author')['login']
        pr.create_time = nodes.get('createdAt')
        pr.body = nodes.get('body')[:1000]
        pr.title = nodes.get('title')
        pr.url = nodes.get('url')
        pr.number = nodes.get('number')
        pr.comments = extract_comments(nodes.get('comments'))
        pr.comments.extend(extract_reviews(nodes.get('reviews')))
        pr.repository = nodes.get("repository")["nameWithOwner"]
        pull_requests.append(pr)
    return pull_requests

def readJson(jfile):
    pull_requests = []
    for path in jfile:
        print(path)
        with open(path, 'r+') as f:
            jfile = json.load(f)
        pr = extract(jfile)
        pull_requests.extend(pr)
    msr_pull_requests = readMSR()
    pull_requests.extend(msr_pull_requests)
    return pull_requests
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


def filter_comments(pull_requests):
    comments = []
    comments_set = set()
    num_pr = set()
    num_reviews = set()
    num_pr_non_author = set()
    num_reviews_non_author = set()
    num_project = set()
    for pr in pull_requests:
        # print("    ", len(pr.comments))
        if pr == None:
            continue
        for c in pr.comments:
            if c.url in comments_set:
                continue
            if not c.has_chatGPT_link:
                continue

            num_pr.add(pr.url)
            num_reviews.add(c.url)
            num_project.add(pr.repository)
            if c.author == pr.author:
                continue
            num_pr_non_author.add(pr.url)
            num_reviews_non_author.add(c.url)
            c.repository = pr.repository
            c.pr_url = pr.url
            c.number = pr.number
            comments.append(c)
            comments_set.add(c.url)
    print("# Collected All Pull Requests", len(num_pr))
    print("# Collected All Reviews", len(num_reviews))
    print("# Collected All Projects", len(num_project))
    print("# PRs with Links", len(num_pr_non_author))
    print("# Comments with Links", len(num_reviews_non_author))
    return comments, comments_set
    pass


def extract_projects(comments):
    projects = set()
    for comment in comments:
        projects.add(comment.repository)
    print("# Projects", len(projects))
    return projects


def extract_prs(comments):
    prs = set()
    for comment in comments:
        prs.add(comment.pr_url)
    return prs


def readMSR():
    msr = set()
    with open('msr.txt') as f:
        for line in f:
            msr.add(line.replace("\n", ""))
    prs = {}

    for m in msr:
        c = Comment()
        c.url = m
        c.pr_url = m.split("#")[0]
        _ = c.pr_url.replace("https://github.com/", "").split("/pull/")
        c.repository = _[0]
        c.number = _[1]
        c.has_chatGPT_link = True
        c.author = "comment_tmp"

        # print(c.pr_url,c.repository,c.number)
        pr = prs.get(c.pr_url, None)
        if pr is None:
            pr = PullRequestData()
            pr.pr_url = c.pr_url
            pr.repository = c.repository
            pr.number = c.number
            pr.author = "pr_tmp"
        pr.comments.append(c)
        prs[c.pr_url] = pr

    return prs.values()
    pass


if __name__ == '__main__':

    filePath = getFilePath()
    print(filePath)
    # path = './data/day/data_2023-05-27T00:00:00_3.json'
    all_pull_requests = readJson(filePath)


    ## INFO
    comments, comments_set = filter_comments(all_pull_requests)

    prs = extract_prs(comments)
    projects = extract_projects(comments)

    with open("links.csv", "w") as o:
        for c in comments:
            o.write(f"{c.url}\n")

