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
    newErrorTimes = []
    for time in errorTime:
        for hour in range(24):
            hour = str(hour).zfill(2)
            newErrorTimes.append(str(time)+"T"+hour+":00:00")
    return newErrorTimes

def main():
    errorTime = readFile("errors_per_day.txt")
    errorStartHours,errorEndHours = delayHour(errorTime)
    for start ,end in zip(errorStartHours,errorEndHours):
        print(start)
        print(end)
        run(start, end, 'hour')

if __name__ == '__main__':
    main()
