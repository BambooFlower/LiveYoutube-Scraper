# -*- coding: utf-8 -*-
"""
Scrape using raw requests.
Inspired by https://github.com/LinaTsukusu/youtube-chat
"""

from requests import session
import json
import re
from datetime import date
from datetime import datetime
from time import time
from time import sleep
import os


headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}

s = session()


class Scraper():
    def __init__(self,videos,output_path = os.getcwd(), user_agent=None,headers=None):
        self.s = session()
        self.videos = videos
        self.output_path = output_path
        self.comment_output_path = output_path
        self.comment_timeout = 10  # Timeout within scrape stats loop
        self.comment_prescrape_time = 60*60  # Minimum time before the start of the stream
        self.comment_time_step = 30  # Time step of comment scrape
        self.jsons = []
        self.inner_json = []
        
        if not headers is None:
            s.headers = headers
        if not user_agent is None:
            s['User-Agent'] = user_agent
            
    def extract_jsons(self,html):
        JSON = re.compile('window\[\"ytInitialData\"\] = ({.*?});', re.DOTALL)
        matches = JSON.search(html)
        json_match = matches[0].replace(';','').replace('window["ytInitialData"] = ','')
        self.jsons = json.loads(json_match)
        
#        inner_tmp = self.jsons['args']['player_response']
#        self.inner_json = json.loads(inner_tmp)
        with open('json.txt','w') as f:
            f.write(json.dumps(self.jsons))
        print("done")

    def get_stats(self,video_id,video_c=0):
        url = 'https://m.youtube.com/watch?v={}'.format(video_id)
        r = self.s.get(url)
        print(url,s.headers)
#        self.extract_jsons(r.text)
        
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
                  'is-streaming':None
                  }
    
        output['status-code'] = r.status_code
        if r.status_code != 200:
            with open('o.txt','w') as f:
                f.write(r.text)
            print('Error {}'.format(r.status_code))
            output['is-live'] = False
            return output
        waiting_list = re.findall('text":"[0-9,]+ waiting"',r.text)
        watching_list = re.findall('[0-9,]+ watching now',r.text)
        likes_list = re.findall('[,0-9]+ likes',r.text)
        dislikes_list = re.findall('[,0-9]+ dislikes',r.text)
        with open("output.txt","w",encoding='utf-8') as f:
            f.write(r.text)
            
        
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
            is_streaming = False
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
            is_streaming = True
            is_live = True
            next_check = time() + self.comment_time_step
        
        output['is-live'] = is_live
        output['next-check'] = next_check
        output['is-streaming'] = is_streaming
        
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
                        data_to_write= {'channel':   data['channel'],
                                        'time':      data['time'],
                                        'viewers':   data['viewers'],
                                        'likes':     data['likes'],
                                        'dislikes':  data['dislikes'],
                                        'video_c':   data['video_c'],
                                        'streaming': data['is-streaming']
                                        }
                        write_file('{}/{}.txt'.format(self.comment_output_path,today),data_to_write)
                        
                        if data['is-streaming']:
                            print_msg = "Channel(Started):{}\tviewers:{}\tlikes:{}\tdislikes:{}".format(data['channel'],data['viewers'],data['likes'],data['dislikes'])
                        else:
                            print_msg = "Channel(Not Started):{}\tviewers:{}\tlikes:{}\tdislikes:{}".format(data['channel'],data['viewers'],data['likes'],data['dislikes'])
                        print(print_msg)
        
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
#            {'id':'wvlj_Z50MuA',
#            'count':0,
#            'name':'other',
#            'next-check':None},
#             
#            {'id':'D6KMZJxdmcw',
#            'count':0,
#            'name':'echo',
#            'next-check':None},
            
#            {'id':'ZmKi-2InLL0',
#            'count':1,
#            'name':'echo',
#            'next-check':None},
#             
#             
#            {'id':'TIsqcWjmx_o',
#            'count':2,
#            'name':'echo',
#            'next-check':None},
#               
#               
#            {'id':'nv68SmtzkVk',
#            'count':3,
#            'name':'echo',
#            'next-check':None},
#               
#            {'id':'T3DaZ9CI5ug',
#            'count':4,
#            'name':'echo',
#            'next-check':None},
#             
#            {'id':'lFfQpJpuJCk',
#            'count':5,
#            'name':'echo',
#            'next-check':None},
#             
#            {'id':'14-RGfKD8oo',
#            'count':6,
#            'name':'echo',
#            'next-check':None},
#             
#            {'id':'89gQF0L_PUE',
#            'count':7,
#            'name':'echo',
#            'next-check':None},
             
            {'id':'eIHsDaTWnQI',
            'count':0,
            'name':'dojd',
            'next-check':None},

#            {'id':'cwtiC73RmXQ',
#            'count':0,
#            'name':'solovey',
#            'next-check':None},
#             
#            {'id':'LxjCNLhX0f8',
#            'count':1,
#            'name':'solovey',
#            'next-check':None},
#             
#            {'id':'xnLa1BU9JBo',
#            'count':2,
#            'name':'solovey',
#            'next-check':None}, 
#                          
#             {'id':'fDZS1k6a_4M',
#            'count':0,
#            'name':'vremya',
#            'next-check':None},
#              
#            {'id':'r9OW8GyULfc',
#            'count':1,
#            'name':'vremya',
#            'next-check':None},
#                          
#                          
#            {'id':'zVvSyDta5es',
#            'count':2,
#            'name':'vremya',
#            'next-check':None},
#             
#            {'id':'7SVFEP-eFOM',
#            'count':3,
#            'name':'vremya',
#            'next-check':None}, 
#             
##             
#              {'id':'k-lp63OJdFs',
#            'count':0,
#            'name':'nash-dom',
#            'next-check':None},
##             
#            {'id':'FNvX7S9jA7o',
#            'count':0,
#            'name':'football',
#            'next-check':None},
#             
#            {'id':'T-0mC6lttAs',
#            'count':0,
#            'name':'navalny',
#            'next-check':None},
#             
#             
#            {'id':'yv-PUK_d-_4',
#            'count':0,
#            'name':'russia 1',
#            'next-check':None},
#             
#             
#             {'id':'ciQxYqzVzIA',
#            'count':0,
#            'name':'RBK',
#            'next-check':None},
#              
#            {'id':'BpcpekYkwlg',
#            'count':1,
#            'name':'dojd',
#            'next-check':None},
            
               


         ]

S = Scraper(videos=videos,
             #output_path=os.getcwd() + '/Output/Stats',
            headers=headers)
S.scrape_stats()