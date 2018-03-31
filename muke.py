# -*- coding=utf-8 -*-

import traceback
import re
import requests
import time
import json
import os

class SCMuke(object):
    def __init__(self):

        self.filePath = ''
        self.lessonID = ''
        self.lessonName = ''
        self.batchId = ''
        self.httpSessionId = ''
        self.username = '*****'
        self.password = '*****'
        self.session = requests.Session()
        self.lessonMenuText = ''
        self.lessonList = []


    def scrapy(self, lessonID, lessonName):
        self.lessonID = lessonID
        self.lessonName = lessonName
        self.initFilePath()
        self.getHttpSessionIDByAccessMuke()
        self.setCookieByLogin()
        self.lessonMenuText = self.getLessonMenu(lessonID)
        self.parseMenu(self.lessonMenuText)

    def initFilePath(self):
        if os.path.isdir(self.filePath) == False:
            self.filePath = os.path.abspath('.') +  '/%s.txt' % self.lessonName
        else:
            self.filePath += '/%s.txt' % self.lessonName
        print('输出路径 - ' + self.filePath)

    def parseMenu(self, menuText):
        if len(menuText) < 10:
            return
        for dict in self.parseLesson(menuText):
            self.lessonList.append(dict)
            jsonStr = json.dumps(self.lessonList).encode('utf-8').decode('unicode-escape')
            with open(self.filePath, 'w') as f:
                f.write(jsonStr)

        print('Finished! HaHaHa!')

    def getLessonMenu(self, lessonNum):
        url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLastLearnedMocTermDto.dwr'
        self.batchId = int(time.time() * 1000)
        print('batchid = ', self.batchId)
        try:
            params = {
                'callCount' : 1,
                'scriptSessionId' : '${scriptSessionId}190',
                'httpSessionId' : self.httpSessionId,
                'c0-scriptName' : 'CourseBean',
                'c0-methodName' : 'getLastLearnedMocTermDto',
                'c0-id' : 0,
                'c0-param0' : 'number:%s' % lessonNum,
                'batchId' : self.batchId
            }
            s = self.session.post(url,data=params)
            s.encoding = s.apparent_encoding
            s.raise_for_status()
            return s.text
        except:
            traceback.print_exc()
            return ''

    def parseLesson(self, text):
        try:
            pat = re.compile(r's[\d]+.contentId.{3}[\d]+;+?')
            rst = pat.findall(text)
            i = 0
            for temp in rst:

                contentId = temp.split('=')[1].split(';')[0]
                num = temp.split('.')[0]
                # 去除掉contentType != 1 的内容
                typePat = re.compile(r'%s.contentType[^;]+' % num)
                type = typePat.findall(text)[0].split('=')[1]
                if int(type) != 1:
                    continue

                dict = {}
                namePat = re.compile(r'%s.name.*";{1}?' % num)
                nameRst = namePat.findall(text)[0]
                title = nameRst.split('\"')[1].encode('utf-8').decode('unicode-escape')
                lIdPat = re.compile(r'%s.id.{3}[\d]+;+?' % num)
                lIdRst = lIdPat.findall(text)[0]
                id = lIdRst.split('=')[1].split(';')[0]

                dict['title'] = title
                dict['id'] = id
                dict['contentId'] = contentId
                dict = self.getDownUrl(dict)
                yield dict

        except:
            traceback.print_exc()

    def getDownUrl(self, dict):
        contentID = dict['contentId']
        id = dict['id']

        url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'
        try:
            params = {
                'callCount': 1,
                'scriptSessionId': '${scriptSessionId}190',
                'httpSessionId': self.httpSessionId,
                'c0-scriptName': 'CourseBean',
                'c0-methodName': 'getLessonUnitLearnVo',
                'c0-id': 0,
                'c0-param0': 'number:%s' % contentID,
                'c0-param1': 1,
                'c0-param2': 0,
                'c0-param3': 'number:%s' % id,
                'batchId': self.batchId
            }
            s = self.session.post(url, data=params)
            s.raise_for_status()
            s.encoding = s.apparent_encoding
            dict = self.parseUrl(s.text, dict)
            return dict
        except:
            traceback.print_exc()
            return dict


    def parseUrl(self, text, dict):
        try:
            sdPat = re.compile(r's[\d]+?.mp4SdUrl[^;]*"')  # 这是标清
            sdRstArr = sdPat.findall(text)
            if len(sdRstArr) > 0 :
                sdRst = sdRstArr[0].split('\"')[1]
                dict['sdUrl'] = sdRst

            hdPat = re.compile(r's[\d]+?.mp4HdUrl[^;]*"')  # 这是高清
            hdRstArr = hdPat.findall(text)
            if len(hdRstArr) > 0:
                sdRst = hdRstArr[0].split('\"')[1]
                dict['hdUrl'] = sdRst

            shdPat = re.compile(r's[\d]+?.mp4ShdUrl[^;]*"')  # 这是超高清
            shdRstArr = shdPat.findall(text)
            if len(shdRstArr) > 0:
                shdRst = shdRstArr[0].split('\"')[1]
                dict['shdUrl'] = shdRst
            return dict
        except:
            return dict


    def setCookieByLogin(self):
        url = 'http://www.icourse163.org/passport/reg/icourseLogin.do'
        param = {
            'returnUrl' : 'aHR0cDovL2ljb3Vyc2UxNjMub3JnLw==',
            'failUrl': 'aHR0cDovL3d3dy5pY291cnNlMTYzLm9yZy9tZW1iZXIvbG9naW4uaHRtP2VtYWlsRW5jb2RlZD1jbUZ1YzJocFkyaGxibWRBTVRZekxtTnZiUT09',
            'savelogin': False,
            'oauthType': '',
            'username': self.username,
            'passwd': self.password,

        }
        s = self.session.post(url, data=param)

    def getHttpSessionIDByAccessMuke(self):
        url = 'http://www.icourse163.org'
        header = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:52.0) Gecko/20100101 Firefox/52.0',
        }
        s = self.session.get(url, headers=header)
        dict = s.cookies.get_dict()
        self.httpSessionId = dict['NTESSTUDYSI']

if __name__ == '__main__':
    lessonNum = '*****'
    lessonName = '*****'
    muke = SCMuke()
    muke.scrapy(lessonNum, lessonName)





