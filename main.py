import requests
import psutil
import socket
import time
import json
import re
import os

ip_url = 'http://47.94.255.161:1925/addlog'
RTdata_url = 'http://localhost:8085/data.json'
wlt_url = 'http://wlt.ustc.edu.cn/cgi-bin/ip'

def parse_RTdata(j):
    cpu = ' '.join(re.findall('"Text": "CPU Core .*? "Value": "(.*?)",',j))
    gpu = ' '.join(re.findall('"Text": "Temperatures", "Children": \[{"id": \d+, "Text": "GPU Core", "Children": \[], "Min": ".*? °C", "Value": "(.*?)",',j))
    gpu += ' ' + ' '.join(re.findall('"Text": "Fans", .*? "Text": "GPU Fan", .*? "Value": "(.*?)",',j))
    return cpu,gpu

#开通网络通
def open_wlt():
    print('正在设置网络通')
    #获取校内ip
    req1 = requests.get(wlt_url)
    req1.encoding = 'gb2312'
    schoolIP = re.findall('<td width=290>(.*?) </td>', req1.text)[0]
    #登录
    login_data = {
        'cmd': 'login',
        'url': 'URL',
        'name': 'nnnn',
        'ip': schoolIP,
        'password': 'ppppp',
        'savepass': 'on',
        'go': '%B5%C7%C2%BC%D5%CA%BB%A7'
        }
    req2 = requests.post(wlt_url, data=login_data)
    cookie_rn = req2.headers['Set-Cookie']#获取rn
    #开通网络
    set_url = wlt_url + '?cmd=set&url=URL&type=0&exp=0&go=+%BF%AA%CD%A8%CD%F8%C2%E7+'#type为出口，exp为时长
    set_headers = {
                'Host': 'wlt.ustc.edu.cn',
                'Referer': 'http://wlt.ustc.edu.cn/cgi-bin/ip',
                'Cookie': 'name=nnnn; password=ppppp; ' + cookie_rn,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
                }
    req3 = requests.get(set_url, headers=set_headers)
    req3.encoding = 'gb2312'
    set_info = re.findall('<td>(信息.*?)<p>', req3.text)[0]
    print(set_info)

def set_WiFi():
    print('正在连接eduroam')
    os.system('netsh wlan connect name=eduroam ssid=eduroam interface="WLAN"')#连接eduroam
    os.system('netsh wlan connect name=eduroam ssid=eduroam interface="WLAN 2"')#连接eduroam

def set_VPN():
    print('正在设置VPN')
    os.system('rasdial "腾讯云" VPN Vguest123')


error_count = 0
time.sleep(10)
while True:
    #cpu_usage = psutil.cpu_percent()
    hostname = socket.gethostname()
    IP_list = socket.gethostbyname_ex(hostname)[-1]
    #print(cpu_usage)
    try:
        r2 = requests.get(RTdata_url)
        RTdata = parse_RTdata(r2.text)
        r2t = r2.text
    except:
        RTdata = (str(psutil.cpu_percent()), 'NOdata')
        r2t = '数据获取失败'

    data = {'ip':str(IP_list),
        'cpu':RTdata[0],
        'gpu':RTdata[1],
        'RTdata':r2t}
    try:
        r1 = requests.post(ip_url, data=data)
    except:
        print('network error')
        try:
            open_wlt()
        except:
            print('网络通也上不去啦')
            set_WiFi()
            time.sleep(15)
            set_VPN()
            try:
                open_wlt()
            except:
                pass
        else:
            set_VPN()
    else:
        print('success')
    time.sleep(30)