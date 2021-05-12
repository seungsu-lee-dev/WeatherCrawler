# -*- coding: utf-8 -*-

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from urllib.request import urlopen, Request
import urllib
import bs4

import socket

import schedule
import threading
import time
from datetime import datetime, timedelta

time_list = []
alarm_bool = True
isSocketActive = False
#input_string = ""
input_location = ''

class crawling:
    location = ''
    def __init__(self, location):
        self.location = location
        enc_location = urllib.parse.quote(location + '+날씨')

        url = 'https://search.naver.com/search.naver?ie=utf8&query='+ enc_location

        req = Request(url)
        page = urlopen(req)
        html = page.read()
        self.soup = bs4.BeautifulSoup(html,'html5lib')

    def crawling_setting(self, location):
        enc_location = urllib.parse.quote(location + '+날씨')

        url = 'https://search.naver.com/search.naver?ie=utf8&query='+ enc_location

        req = Request(url)
        page = urlopen(req)
        html = page.read()
        self.soup = bs4.BeautifulSoup(html,'html5lib')

    def crawling_enable(self, location):
        self.crawling_setting(location)
        if self.soup.find('h2', class_='api_title').text == '날씨정보':
            self.location = location
            return location
        else:
            location = location + "지역정보가 올바르지 않습니다."
            return location

    def crawling_final(self):
        self.crawling_setting(self.location)
        crawling_text="""\
현재 {} 날씨는 {} .
현재 온도는 {}도, 최저 온도는 {}도, 최고 온도는 {}도입니다.
체감 온도는 {}도, """.format(self.location, self.soup.find('ul', class_='info_list').find('p', class_='cast_txt').text, self.soup.find('p', class_='info_temperature').find('span', class_='todaytemp').text\
, self.soup.find('span', class_='min').find('span', class_='num').text, self.soup.find('span', class_='max').find('span', class_='num').text, \
self.soup.find('span', class_='sensible').find('span', class_='num').text)

        if '강수량' in self.soup.find('ul', class_='info_list').text:
            crawling_text = crawling_text + """{}입니다.
오전 강수확률은 {}%, 오후 강수확률은 {}%입니다.
{}입니다.
""".format(self.soup.find('ul', class_='info_list').find('span', class_='rainfall').text, \
self.soup.find('span', class_='point_time morning').find('span', class_='rain_rate').find('span', class_='num').text, \
self.soup.find('span', class_='point_time afternoon').find('span', class_='rain_rate').find('span', class_='num').text, \
self.soup.find('dl', class_='indicator').text)
        else:
            crawling_text = crawling_text + """{}입니다.
오전 강수확률은 {}%, 오후 강수확률은 {}%입니다.
{}입니다.
""".format(self.soup.find('ul', class_='info_list').find('span', class_='indicator').text, \
self.soup.find('span', class_='point_time morning').find('span', class_='rain_rate').find('span', class_='num').text, \
self.soup.find('span', class_='point_time afternoon').find('span', class_='rain_rate').find('span', class_='num').text, \
self.soup.find('dl', class_='indicator').text)
        weather_mail(crawling_text)

cr = crawling('안동 송천동')

def weather_mail(mail_text):
    sender_email = "sloth19g@gmail.com"
    receiver_email = "sag120@naver.com"
    password = "saea2011"

    message = MIMEMultipart("alternative")
    message["Subject"] = "오늘의 날씨"
    message["From"] = sender_email
    message["To"] = receiver_email

    part1 = MIMEText(mail_text, "plain")

    message.attach(part1)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
            )

    now_data = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M:%S')
    print('run - ' + str(now_data) + ' ' + str(now_time))

def schedule_alarm():
    global alarm_bool
    for t in range(len(time_list)):
        schedule.every().day.at(time_list[t]).do(cr.crawling_final)
    while alarm_bool:
        schedule.run_pending()
        time.sleep(1)

def socket_server():
    global isSocketActive
    isSocketActive = True
    HOST = ""
    PORT = 8888
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print ('Socket created')
    s.bind((HOST, PORT))
    print ('Socket bind complete')
    s.listen(1)
    print ('Socket now listening')
    #파이 컨트롤 함수
    def do_some_stuffs_with_input(input_string):
        #라즈베리파이를 컨트롤할 명령어 설정
        global alarm_bool
        global isSocketActive
        global input_location
        if input_string.endswith('읍') or input_string.endswith('면') or input_string.endswith('동'):
            input_location = input_string
            input_string = cr.crawling_enable(input_string)
            input_string = input_string + " 지역으로 설정하였습니다."
            time.sleep(5)
        elif input_string == "날씨":
            input_string = "날씨 이메일을 발송했습니다."
            cr.crawling_final()
            #파이 동작 명령 추가할것
        elif input_string == "시간":
            if not time_list:
                input_string = "설정된 시간이 없습니다."
            else:
                input_string = "알림시간: "
                for i in time_list:
                    input_string += i
                    input_string += ' '
            print(schedule.jobs)
        elif ':' in input_string:
            alarm_bool = False
            time.sleep(1)
            schedule.clear(tag=None)
            
            if input_string in time_list :
                time_list.remove(input_string)
                alarm_thread = threading.Thread(target=schedule_alarm)
                alarm_bool = True
                alarm_thread.start()
                input_string = input_string + " 시간 삭제하였습니다."
            else:
                time_list.append(input_string)
                alarm_thread = threading.Thread(target=schedule_alarm)
                alarm_bool = True
                alarm_thread.start()
                input_string = input_string + " 시간으로 알림설정합니다."
            print(schedule.jobs)
        elif input_string == "종료":
            input_string = "소켓을 닫습니다."
            s.close()
            isSocketActive=False
        else :
            input_string = input_string + " 없는 명령어 입니다."
        print('현재 스레드 수는 ' + str(threading.active_count()))
        return input_string

    while isSocketActive:
        #접속 승인
        conn, addr = s.accept()
        print("Connected by ", addr)

        #데이터 수신
        data = conn.recv(1024)
        data = data.decode("utf8").strip()
        if not data: break
        print("Received: " + data)

        #수신한 데이터로 파이를 컨트롤
        res = do_some_stuffs_with_input(data)
        print("파이 동작 :" + res)

        #클라이언트에게 답을 보냄
        conn.sendall(res.encode("utf-8"))
        #연결 닫기
        conn.close()

socket_server()






















