# -*- coding: utf-8 -*-
import os
from YTLiveScrape.live_chat_worker import LiveMachine
import time

livestream_id = 'wO1VonWNV9Q'  # from e.g. https://www.youtube.com/watch?v=3GgSphuyBiY

L = LiveMachine(livestream_id)

# Start stats loop
L.request_stats()
# Start comments loop
L.request_comments()


def write_file(filename,data):
    if not os.path.exists(filename):
        with open(filename,'w',encoding='utf-8') as f:
            line = ''
            for key in data.keys():
                line += key + "\t"
            line = line[:-1]
            line +=  "\n"
            f.write(line)
    else:
        with open(filename,'a',encoding='utf-8') as f:
            line = ''
            for key in data.keys():
                line += data[key].replace("\n","") + "\t"
            line = line[:-1]
            line +=  "\n"
            f.write(line)

#filename = 'dojd'
#
#for i in range(5):
#    comments = L.get_comments()
#    for comment in comments:
##        write_file('{}views.txt'.format(filename),comment)
#        print(commen
#    time.sleep(5)