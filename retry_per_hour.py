# TODO: errors_day.txt読み込み
import datetime
import time
from main_ import run
from main_ import convertTimeFromString


# TODO: 時間ごとにやる

def exactTime(line):
    line = line[:10]
    return line
def readFile(filename):
    errorTime = []
    with open(filename, 'r') as f:
        for line in f :
            errorTime.append(exactTime(line))
    return errorTime

def delayHour(errorTime):
    newErrorStartTimes = []
    newErrorEndTimes = []
    for time in errorTime:
        for hour in range(24):
            newErrorStartTimes.append(str(time)+"T"+str(hour).zfill(2)+":00:00")

            if (str(hour+1) == '24'):
                original_date = datetime.datetime.strptime(time,"%Y-%m-%d")
                next_day = original_date + datetime.timedelta(days=1)
                next_day_str = next_day.strftime("%Y-%m-%d")
                newErrorEndTimes.append(next_day_str + "T00:00:00")
                continue

            newErrorEndTimes.append(str(time) + "T" + str(hour+1).zfill(2) + ":00:00")
    print(newErrorStartTimes)
    print(newErrorEndTimes)
    return newErrorStartTimes,newErrorEndTimes

def main():
    errorTime = readFile("errors_per_day.txt")
    errorStartHours,errorEndHours = delayHour(errorTime)
    for start ,end in zip(errorStartHours,errorEndHours):
        print(start)
        print(end)
        run(start, end, datetime.timedelta(hours=1), 'errors_per_hour.txt')

if __name__ == '__main__':
    main()
