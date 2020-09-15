# -*- coding: utf-8 -*-
import os
from YTLiveScrape.live_chat_worker import LiveMachine
import time
from datetime import datetime
import threading

todaydate = datetime.today().strftime('%Y-%m-%d')

live_stream_ids = [#'38ICBymhD9Q',
                   #'Ed5euGd4s4o',
                   #'NeST_YmwOuc','KFSx2YjNgno',
                   #'zeOCUu6IVVg','M3BIFYIX_sE',
                   #'G3DXNgVNPII',
                   '-lo55cFYKdA'
                   ]

LiveMachines = []
for c,live_stream_id in enumerate(live_stream_ids):
    print('initialising machine {} out of {}'.format(c+1,len(live_stream_ids)))
    if c > 1:
        cookies = LiveMachines[0].session.cookies
    else:
        cookies = None
    LiveMachines.append(LiveMachine(live_stream_id,cookies=cookies))
    time.sleep(10)

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

run = True

def stop():
    global run
    run = False
    for L in LiveMachines:
        L.stop_scrape()

def update_comments():
    filename = 'comments/{}'.format(todaydate)
    
    while 1:
        if not run:
            break
        for L in LiveMachines:
            comments = L.get_comments()
            for comment in comments:
                comment['channel'] = L.channel_id
                comment['channel_name'] = L.video_author
                comment['video'] = L.video_id
                write_file('{}.txt'.format(filename),comment)
            if L.comments_enabled:
#                print('{} has {} new comments'.format(L.video_id,len(comments)))
                pass
        time.sleep(5)
        
def update_viewers():
    filename = 'viewers/{}'.format(todaydate)
    
    while 1:
        if not run:
            break
        for L in LiveMachines:
            stats = L.get_stats()
            for stat in stats:
                stat['channel_id'] = L.channel_id
                stat['channel_name'] = L.video_author
                stat['video'] = L.video_id
                write_file('{}.txt'.format(filename),stat)
    #        print(commen)
        time.sleep(5)
        
x = threading.Thread(target=update_comments)
y = threading.Thread(target=update_viewers)
x.start()
y.start()

#stop()