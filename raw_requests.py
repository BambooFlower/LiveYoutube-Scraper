# -*- coding: utf-8 -*-
"""
Scrape using raw requests.
Inspired by https://github.com/LinaTsukusu/youtube-chat
"""

from requests import session
import re
from datetime import date
from datetime import datetime
from time import time
from time import sleep
import os


#headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}

s = session()


class Scraper():
    def __init__(self,videos,output_path = os.getcwd(), user_agent=None,headers=None):
        self.s = session()
        self.videos = videos
        self.output_path = output_path
        self.comment_output_path = os.getcwd()
        self.comment_timeout = 10  # Timeout within scrape stats loop
        self.comment_prescrape_time = 60*60  # Minimum time before the start of the stream
        self.comment_time_step = 30  # Time step of comment scrape
        
        if not headers is None:
            s.headers = headers
        if not user_agent is None:
            s['User-Agent'] = user_agent

    def get_stats(self,video_id,video_c=0):
        url = 'https://youtube.com/watch?v={}'.format(video_id)
        r = self.s.get(url)
        
        output = {'channel':video_id,
                  'next-check':None,
                  'is-live':False,
                  'status-code':None,
                  'time':time(),
                  'viewers':None,
                  'likes':None,
                  'dislikes':None,
                  'video_c':video_c,
                  'next-check':None,
                  }
    
        output['status-code'] = r.status_code
        if r.status_code != 200:
            print('Error {}'.format(r.status_code))
            output['is-live'] = False
            return output
        waiting_list = re.findall('text":"[0-9,]+ waiting"',r.text)
        watching_list = re.findall('[0-9,]+ watching now',r.text)
        likes_list = re.findall('[,0-9]+ likes',r.text)
        dislikes_list = re.findall('[,0-9]+ dislikes',r.text)
#        with open("output.txt","w",encoding='utf-8') as f:
#            f.write(r.text)
            
        
        channel = re.findall('[cC]hannelName":".*?"',r.text)[0].replace('"','').replace('hannelName:','').replace('c','').replace('C','')
        output['channel'] = channel
            
        num_viewers = 0
        if waiting_list != []:
            num_viewers = waiting_list[0].replace(' waiting','').replace(',','').replace('text":"','').replace('"','')
        elif watching_list != []:
            num_viewers = watching_list[0].replace(' watching now','').replace(',','')#.replace('simpleText":"','').replace('"','')
        else:
            return output
        
        output['viewers'] = num_viewers
        
        if 'false' in re.findall('"isLiveNow":[a-z]+',r.text)[0]:
            if re.findall('"endTimestamp":"[0-9\-T\+:]+"',r.text) != []:
                is_live = False
                next_check = None
            else:
                is_live = True
                timestamp = eval(re.findall('scheduledStartTime":"[0-9]+"',r.text)[0].replace('scheduledStartTime":"','').replace('"',''))
    
                if timestamp - time() > self.comment_prescrape_time:
                    next_check = timestamp
                else:
                    next_check = time() + self.comment_time_step
                    
        else:
            is_live = True
            next_check = time() + self.comment_time_step
        
        output['is-live'] = is_live
        output['next-check'] = next_check
        
        try:        
            num_likes = likes_list[0].replace(' likes','').replace(',','')
        except IndexError:
            num_likes = 0
        try:
            num_dislikes = dislikes_list[0].replace(' dislikes','').replace(',','')
        except IndexError:
            num_dislikes = 0
            
        output['likes'] = num_likes
        output['dislikes'] = num_dislikes
            
        
        return output
    
    def scrape_stats(self):
        first_loop = True
        while 1:
            in_to_rem = []
            for c,video in enumerate(self.videos):
                video_id = video['id']
                video_c = video['count']
                
                
                if video['next-check'] is None:
                    pass
                else:
                    d = float(video['next-check'])-time()
                    if 0 < d < self.comment_time_step:
                        print('will check {} in {:.2f} seconds'.format(video['name'],(float(video['next-check'])-float(time()))))
                        continue
                    elif d > self.comment_prescrape_time:
                        print('will check {} in {:.2f} minutes'.format(video['name'],abs(60-(float(video['next-check'])-float(time()))/60)))
                        continue
                    
                today = date.today()
                data = self.get_stats(video_id,video_c=video_c)
                
                if not data['is-live']:
                    if data['status-code'] == 200:
                        print('Stream from "{}" at "v={}" is Offline'.format(data['channel'],video_id))
                        in_to_rem.append(self.videos.index(video))
                        self.videos[c]['next-check'] = data['next-check']
                        self.videos[c]['name'] = data['channel']
                        
                    else:
                        print('bad error from YouTube {} :('.format(data['status-code']))
                        exit(-1)
                else:
                    self.videos[c]['next-check'] = data['next-check']
                    self.videos[c]['name'] = data['channel']
                    if not first_loop:
                        write_file('{}/{}.txt'.format(self.comment_output_path,today),data)
                        print("Channel:{}\tviewers:{}\tlikes:{}\tdislikes:{}".format(data['channel'],data['viewers'],data['likes'],data['dislikes']))
        
            first_loop = False
            v = [i for i in range(len(self.videos))]
    
            tmp_list = self.videos[:]
            self.videos = []
            for vi in v:
                if not vi in in_to_rem:
                    self.videos.append(tmp_list[vi])
            print("{}\n".format(datetime.now()))
            if self.videos == []:
                break
            sleep(self.comment_timeout)

def write_file(filename,data):
#    print(filename)
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
             
              {'id':'xTLY3CIQ6BM',
            'count':0,
            'name':'solovey',
            'next-check':None},

                

         ]

S = Scraper(videos=videos,output_path=os.getcwd() + '/Output/Comments')
S.scrape_stats()