# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 16:54:14 2020

@author: vz237
"""

from requests import session
import re
from datetime import date
from datetime import datetime
from time import time
from time import sleep
import os


#https://github.com/LinaTsukusu/youtube-chat

#liveid = 'mg7FweYjasE'
#headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
#channel = 'UC3ZODI-xZfdPanPP6tKUg9g'
#url = 'https://www.youtube.com/channel/{}/live'.format(channel)
#
s = session()
#s.get('https://youtube.com')
#s.headers = headers
#
#
#url = 'https://www.youtube.com/live_chat?v={}&pbj=1'.format(liveid)
#r = s.get(url)
##matches = re.findall('"watchEndpoint":{"videoId":"[aA-zZ0-9]+',r.text)

# Find number of people watching


video_id = 'qKfcKzxJCcg' # Navalny
#video_id = 'TIRFThJW-V8' # Solovey
#video_id = '0M08QN0b2sw' # solovey 2
video_id = 'fRgUKrT6F6k' # dojd

videos = [ 
            {'id':'Q0ZuA_qBCxQ',
            'count':0,
            'name':'echo',
            'next-check':None},

            {'id':'yF5j7tg6eqY',
            'count':1,
            'name':'solovey',
            'next-check':None},
             
             {'id':'YiPo-vmn8yQ',
            'count':0,
            'name':'dojd',
            'next-check':None},
             
              {'id':'NM8UMuTcF_A',
            'count':0,
            'name':'navalny',
            'next-check':None},
              
              
#             {'id':'40fFYvNiM-4',
#            'count':0,
#            'name':'RBK',
#            'next-check':None},
             
#            {'id':'wyDy1rZnbQc',
#            'count':1,
#            'name':'vremya',
#            'next-check':None},
              
             
         ]
video_id = 'nh28agdnOc8' # Nashtoyashee Vremya
video_c = 1


#s.headers['User-Agent'] = 'curl/7.64.0'
#s.headers['Accept'] = '*/*'
#

def get_data(video_id,video_c=0):
    url = 'https://youtube.com/watch?v={}'.format(video_id)
    r = s.get(url)
#    headers = {'User-Agent':'curl/7.64.0',
#               'Accept':'*/*',
#               'Host':'m.youtube.com'}
#    s.headers = headers
#    print(s.headers,url)
    if r.status_code != 200:
        print('Error {}'.format(r.status_code))
        return {'channel':video_id,'next-check':None},False,r.status_code
    waiting_list = re.findall('text":"[0-9,]+ waiting"',r.text)
    watching_list = re.findall('[0-9,]+ watching now',r.text)
    likes_list = re.findall('[,0-9]+ likes',r.text)
    dislikes_list = re.findall('[,0-9]+ dislikes',r.text)
#    print(re.findall('[cC]hannelName":".*?"',r.text),r.text)
    with open("output.txt","w",encoding='utf-8') as f:
        f.write(r.text)
    channel = re.findall('[cC]hannelName":".*?"',r.text)[0].replace('"','').replace('hannelName:','').replace('c','').replace('C','')
        
    num_viewers = 0
    if waiting_list != []:
        num_viewers = waiting_list[0].replace(' waiting','').replace(',','').replace('text":"','').replace('"','')
    elif watching_list != []:
        num_viewers = watching_list[0].replace(' watching now','').replace(',','')#.replace('simpleText":"','').replace('"','')
    else:
        return {'channel':channel,'next-check':None},False,r.status_code
    
    if 'false' in re.findall('"isLiveNow":[a-z]+',r.text)[0]:
        #if not '"endTimestamp"' in r.text:
        if re.findall('"endTimestamp":"[0-9\-T\+:]+"',r.text) != []:
            is_live = False
            next_check = None
        else:
            is_live = True
            timestamp = eval(re.findall('scheduledStartTime":"[0-9]+"',r.text)[0].replace('scheduledStartTime":"','').replace('"',''))
#            print(timestamp - time())
            if timestamp - time() > 60*60:
#                print(1)
                next_check = timestamp
            else:
#                print(0)
                next_check = time() + 30
                
    else:
        is_live = True
        next_check = time() + 30
    
    try:        
        num_likes = likes_list[0].replace(' likes','').replace(',','')
    except IndexError:
        num_likes = 0
    try:
        num_dislikes = dislikes_list[0].replace(' dislikes','').replace(',','')
    except IndexError:
        num_dislikes = 0
        
#    if is_live:
#        next_check = time() + 30
#    else:    
#        # Find the start time
#        timestamp = eval(re.findall('scheduledStartTime":"[0-9]+"',r.text)[0].replace('scheduledStartTime":"','').replace('"',''))
#        
#        diff_start = time() - timestamp
#        if diff_start < -60*60:
#            next_check = timestamp - 60*60
#        else:
#            next_check = time() + 30
    
    output = {'time':str(time()),
              'viewers':str(num_viewers),
              'likes':str(num_likes),
              'dislikes':str(num_dislikes),
              'channel':channel,
              'video_c':str(video_c),
              'next-check':str(next_check)}

    return output,is_live,r.status_code

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
            line += data[key].replace("\n","") + "\t"
        line = line[:-1]
        line +=  "\n"
        f.write(line)

first_loop = True
while 1:
    in_to_rem = []
    for c,video in enumerate(videos):
        video_id = video['id']
        video_c = video['count']
        
        
        if video['next-check'] is None:
            pass
        else:
            d = float(video['next-check'])-time()
#            print(d,video['name'])
            if 0 < d < 30:
                print('will check {} in {:.2f} seconds'.format(video['name'],(float(video['next-check'])-float(time()))))
                continue
            elif d > 60*60:
                print('will check {} in {:.2f} minutes'.format(video['name'],abs(60-(float(video['next-check'])-float(time()))/60)))
                continue
        
#        if -30 <= d <= 0:
            
            
        today = date.today()
        data,is_live,code = get_data(video_id,video_c=video_c)
        
        if not is_live:
            if code == 200:
                print('Stream from "{}" at "v={}" is Offline'.format(data['channel'],video_id))
                in_to_rem.append(videos.index(video))
                videos[c]['next-check'] = data['next-check']
                videos[c]['name'] = data['channel']
                
            else:
                print('bad error from YouTube {} :('.format(code))
                exit(-1)
        else:
            videos[c]['next-check'] = data['next-check']
            videos[c]['name'] = data['channel']
            if not first_loop:
                write_file('PythonData/{}.txt'.format(today),data)
                print("Channel:{}\tviewers:{}\tlikes:{}\tdislikes:{}".format(data['channel'],data['viewers'],data['likes'],data['dislikes']))

    first_loop = False
    v = [i for i in range(len(videos))]
#    print(next_check)
    tmp_list = videos[:]
    videos = []
    for vi in v:
        if not vi in in_to_rem:
            videos.append(tmp_list[vi])
    print("{}\n".format(datetime.now()))
    if videos == []:
        break
#    break
    sleep(10)