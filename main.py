import time

import requests
import json
import mysql.connector

import json



# usage
# python3 github.py | jq . -C | less -R

# token
token = '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'
token2 = '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'
token3 = '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'
token4 = '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'

# endpoint
endpoint = 'https://api.github.com/graphql'

# ratelimit
# https://developer.github.com/v4/query/  ->  rateLimit
# https://developer.github.com/v4/object/ratelimit/

def create_querry(startdate, enddate):
    test01 = {'query': """
        query ($startdate:String!,$enddate:String!){
            search(
                query: "https://chat.openai.com/share/ is:public is:pr pr created:$startdate..$enddate"
                type: ISSUE
                first: 60
            ) {
            edges {
              node {
                ... on PullRequest {
                  number
                  title
                  repository {
                    nameWithOwner
                    primaryLanguage {
                      name
                    }
                  }
                  createdAt
                  mergedAt
                  url
                  state
                  author {
                    login
                  }
                  editor {
                    login
                  }
                  body
                  reviews(first: 100) {
                    edges {
                      node {
                        state
                        bodyText
                        comments(first: 100) {
                            edges {
                              node {
                                    bodyText
                                    author {
                                        login
                                    }
                                    url
                                originalCommit {
                                    abbreviatedOid
                                    authoredDate
                                }
                                }
                          }
                        }
                     }
                    }
                  }
                }
              }
              textMatches {
                property
              }
            }
            pageInfo {
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
            issueCount
          }
        }
        variables{
            "startdate"
        }
          """
                  }
    return test01

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def post(query,token):
    headers = {"Authorization": "bearer " + token}
    res = requests.post(endpoint, json=query, headers=headers)
    if res.status_code != 200:
        raise Exception("failed : {}".format(res.status_code))
    return res.json()

def creatTable(cursor):
    cursor.execute("DROP TABLE IF EXISTS ease_table")
    try:
        cursor.execute("""CREATE TABLE ease_table(
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


def main():
    start = ['2023-09-3','2023-09-10','2023-09-17','2023-09-24','2023-10-3','2023-10-1','2023-10-08','2023-10-15','2023-10-22','2023-10-29','2023-11-05','2023-11-12','2023-11-19','2023-11-26','2023-12-03','2023-12-10','2023-12-17','2023-12-24','2023-12-31','2024-01-07','2024-01-14','2024-01-21','2024-01-28','2024-02-04','2024-02-11','2024-02-18','2024-2-25','2024-03-03']
    end = ['2023-09-10','2023-09-17','2023-09-24','2023-10-3','2023-10-1','2023-10-08','2023-10-15','2023-10-22','2023-10-29','2023-11-05','2023-11-12','2023-11-19','2023-11-26','2023-12-03','2023-12-10','2023-12-17','2023-12-24','2023-12-31','2024-01-07','2024-01-14','2024-01-21','2024-01-28','2024-02-04','2024-02-11','2024-02-18','2024-2-25','2024-03-03','2024-03-10']

    for i  in range(0,len(start)-3,4):
        query = create_querry(start[i], end[i])
        query2 = create_querry(start[i+1], end[i+1])
        query3 = create_querry(start[i+2], end[i+2])
        query4 = create_querry(start[i+3], end[i+3])
    for i in range(30):
        # print('test{}'.format(i))
        res = post(query,token)
        res2 = post(query2, token2)
        res3 = post(query3, token3)
        res4 = post(query4, token4)
        filename = 'querry'+str(i)
        filename2 = 'querry2' + str(i)
        filename3 = 'querry3' + str(i)
        filename4 = 'querry4' + str(i)
        save_json(res,filename)
        save_json(res2, filename2)
        save_json(res3, filename3)
        save_json(res4, filename4)
        time.sleep(3000)
        print('{}'.format(json.dumps(res)))


if __name__ == '__main__':
    connection = mysql.connector.connect(
        host='localhost',
        user='me',
        passwd='goma',
        db='ease')
    cursor = connection.cursor()

    creatTable(cursor)
    main()
