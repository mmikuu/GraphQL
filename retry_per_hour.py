# TODO: errors_day.txt読み込み
from datetime import datetime

from main_ import run

run('2023-09-03T00:00:00', '2024-02-01T00:00:00', datetime.timedelta(hours=1), 'errors_per_hour.txt')

# TODO: 時間ごとにやる
