# -*- coding: utf-8 -*-
import os
from YTLiveScrape.live_chat_worker import LiveMachine
import time
from datetime import datetime
import threading

todaydate = datetime.today().strftime('%Y-%m-%d')

livestream_id = '3GgSphuyBiY'  # from e.g. https://www.youtube.com/watch?v=3GgSphuyBiY
livestream_id = '3GgSphuyBiY'

live_stream_ids = ['3GgSphuyBiY']

LiveMachines = []
for live_stream_id in live_stream_ids:
    LiveMachines.append(LiveMachine(livestream_id))

for L in LiveMachines:    
    if L.has_data:
        # Start stats loop
        L.request_stats()
        if L.comments_enabled:
            # Start comments loop
            L.request_comments()


def find_channel_name(channel_id):
    pass

def write_file(filename,data):
    if not os.path.exists(filename):
        with open(filename,'w',encoding='utf-8') as f:
            line = ''
            for key in data.keys():
                line += key + "\t"
            line = line[:-1]
            line +=  "\n"
            f.write(line)
    with open(filename,'a',encoding='utf-8') as f:
        line = ''
        for key in data.keys():
            tmp = str(data[key])
            line += tmp.replace("\n","") + "\t"
        line = line[:-1]
        line +=  "\n"
        f.write(line)

global run
run = True

def stop():
    global run
    run = False

def update_comments():
    filename = 'comments/{}'.format(todaydate)
    
    while 1:
        if not run:
            break
        for L in LiveMachines:
            comments = L.get_comments()
            for comment in comments:
                comment['channel'] = L.channel_id
                comment['video'] = L.video_id
                write_file('{}.txt'.format(filename),comment)
            print('{} has {} new comments'.format(L.video_id,len(comments)))
        time.sleep(5)
        
def update_viewers():
    filename = 'viewers/{}'.format(todaydate)
    
    while 1:
        if not run:
            break
        for L in LiveMachines:
            stats = L.get_stats()
            for stat in stats:
                stat['channel'] = L.channel_id
                stat['video'] = L.video_id
                write_file('{}.txt'.format(filename),stat)
    #        print(commen)
        time.sleep(5)
        
x = threading.Thread(target=update_comments)
y = threading.Thread(target=update_viewers)
x.start()
y.start()
