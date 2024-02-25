import time

import requests
import json
import mysql.connector

import json



# usage
# python3 github.py | jq . -C | less -R

# token
tokens = []

f = open('tokens.txt', 'r')
while True:
  t = f.readline()
  if t == '':
    break
  tokens.append(t.replace("\n",""))
f.close()
print(tokens)


# endpoint
endpoint = 'https://api.github.com/graphql'

# ratelimit
# https://developer.github.com/v4/query/  ->  rateLimit
# https://developer.github.com/v4/object/ratelimit/

def create_query(startdate, enddate, endCursorId):
    cursor = ""
    if endCursorId:
        cursor=f'after: "{endCursorId}"'
    test01 = {'query': f"""
        query {{
            search(
                query: "https://chat.openai.com/share/ is:public is:pr pr created:{startdate}..{enddate}"
                type: ISSUE
                first: 10
                {cursor}
            ) {{
            edges {{
              node {{
                ... on PullRequest {{
                  number
                  title
                  repository {{
                    nameWithOwner
                    primaryLanguage {{
                      name
                    }}
                  }}
                  createdAt
                  mergedAt
                  url
                  state
                  author {{
                    login
                  }}
                  editor {{
                    login
                  }}
                  body
                  reviews(first: 100) {{
                    edges {{
                      node {{
                        state
                        bodyText
                        comments(first: 100) {{
                            edges {{
                              node {{
                                    bodyText
                                    author {{
                                        login
                                    }}
                                    url
                                originalCommit {{
                                    abbreviatedOid
                                    authoredDate
                                }}
                                }}
                          }}
                        }}
                     }}
                    }}
                  }}
                }}
              }}
              textMatches {{
                property
              }}
            }}
            pageInfo {{
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }}
            issueCount
          }}
        }}
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
    start = ['2023-09-03','2023-09-10','2023-09-17','2023-09-24','2023-10-03','2023-10-01','2023-10-08','2023-10-15','2023-10-22','2023-10-29','2023-11-05','2023-11-12','2023-11-19','2023-11-26','2023-12-03','2023-12-10','2023-12-17','2023-12-24','2023-12-31','2024-01-07','2024-01-14','2024-01-21','2024-01-28','2024-02-04','2024-02-11','2024-02-18','2024-2-25','2024-03-03']
    i = 0
    page_no = 0
    endCursor = None
    while i < len(start)-1:
        query = create_query(start[i], start[i+1], endCursor)
        print(i % len(tokens))
        token = tokens[i % len(tokens)]
        # print('test{}'.format(i))
        res = post(query,token)
        print(res)

        has_next_page = res["data"]["search"]["pageInfo"]["hasNextPage"]
        endCursor = res["data"]["search"]["pageInfo"]["endCursor"]
        print(has_next_page)
        print(endCursor)
        save_json(res,f'data/data_{i}_{page_no}.json')

        if has_next_page:
            page_no += 1
        else:
            i += 1
            page_no = 0
        if i % len(tokens) == 0:
            time.sleep(0.73)#100秒あたり138回アクセスしたい（60*60*1.38=4968<5000)


if __name__ == '__main__':
    # connection = mysql.connector.connect(
    #     host='localhost',
    #     user='me',
    #     passwd='goma',
    #     db='ease')
    # cursor = connection.cursor()
    #
    # creatTable(cursor)
    main()
