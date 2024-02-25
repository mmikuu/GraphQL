import datetime
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
ORIGINAL_BUTCH_SIZE = 10
BUTCH_SIZE = ORIGINAL_BUTCH_SIZE
def create_query(startdate, enddate, endCursorId):
    cursor = ""
    if endCursorId:
        cursor=f'after: "{endCursorId}"'
    test01 = {'query': f"""
        query {{
            search(
                query: "https://chat.openai.com/share/ 
                is:public 
                is:pr 
                pr created:{startdate}..{enddate}"
                type: ISSUE
                first: {BUTCH_SIZE}
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




def convertTimeFromString(s):
    if "T" in s:
        _ = s.split("T")
    elif " " in s:
        _ = s.split(" ")
    else:
        raise

    dates = _[0].split("-")
    times = _[1].split(":")
    return datetime.datetime(int(dates[0]), int(dates[1]), int(dates[2]), int(times[0]), int(times[1]), int(times[2]), 0)


def covert_t_time(t):
    return str(t).replace(" ","T")


def get_delta(unit):
    if unit == "day":
        delta = datetime.timedelta(days=1)
    elif unit == "hour":
        delta = datetime.timedelta(hours=1)
    elif unit == "minute":
        delta = datetime.timedelta(minutes=1)
    else:
        print("Wrong argument")
        raise
    return delta


def run(start_, end_, unit):
    delta = get_delta(unit)



    start = convertTimeFromString(start_)
    end = convertTimeFromString(end_)
    current = start
    it = 0
    page_no = 0
    endCursor = None
    errors = []
    print("=====", current, "=====")
    while current < end:
        print("   ", "---", page_no, "---")
        it += 1
        next = current + delta
        query = create_query(covert_t_time(current),
                             covert_t_time(end),
                             endCursor)
        print("      ", "tokenNo", it % len(tokens))
        token = tokens[it % len(tokens)]
        res = post(query, token)
        print("      ", res)
        if "errors" in res:
            print("ERROR FOUND")
            errors.append(covert_t_time(current)+"\n")
            current = next
            endCursor = None
            page_no = 0
            continue
        has_next_page = res["data"]["search"]["pageInfo"]["hasNextPage"]
        endCursor = res["data"]["search"]["pageInfo"]["endCursor"]
        save_json(res, f'data/{unit}/data_{covert_t_time(current)}_{page_no}.json')
        page_no += 1
        if not has_next_page:
            current = next
            endCursor = None
            page_no = 0
            print("=====", current, "=====")
        if it % len(tokens) == 0:
            print("waiting...")
            time.sleep(0.73)  # 100秒あたり138回アクセスしたい（60*60*1.38=4968<5000)
    with open(f"errors_per_{unit}.txt", 'w') as f:
        f.writelines(errors)

def main():
    global BUTCH_SIZE
    run('2023-05-27T00:00:00', '2024-02-01T00:00:00', 'day')
    # run('2023-10-01T00:00:00', '2023-10-2T00:00:00', 'day')


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
