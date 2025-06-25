import subprocess

import time 
from datetime import datetime

hour = int(input("Enter the hour (0-24) : "))
minute = int(input('Enter the minute (0-60): '))
second =  int(input('Enter the second (0-60): '))
micro_second =  int(input('Enter the micro-second (0-999): '))
time_now = datetime.now()
start_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=micro_second)
delay = (start_time - time_now).total_seconds()

time.sleep(delay - 0.3)
subprocess.run(['python', 'fetch.py'], shell= True)




