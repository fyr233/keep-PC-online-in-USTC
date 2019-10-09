import requests
import psutil
import socket
import time
import json
import re
import os
import sys
from xzqhotspot import manager as hsmanager
import subprocess
from termcolor import colored

ip_url = 'http://47.94.255.***:1925/addlog'
RTdata_url = 'http://localhost:8085/data.json'
wlt_url = 'http://wlt.ustc.edu.cn/cgi-bin/ip'

hsmgr = hsmanager()
os.system('color')

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
        'name': 'nnnnnn',
        'ip': schoolIP,
        'password': 'pppppp',
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
                'Cookie': 'name=nnnnnn; password=pppppp; ' + cookie_rn,
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
	os.system('rasdial "腾讯云" *** *******')

def test_Ping():
    sites = ['eth-cn.dwarfpool.com','xmr-us.dwarfpool.com']
    result = ''
    for each in sites:
        p = subprocess.Popen('ping '+each, shell = True, stdout = subprocess.PIPE)
        p.wait()
        result += each + ':' + re.findall('平均 = (.*?ms)', p.stdout.read().decode('gbk'))[0] + ' '
    return result

def fix_5G():
    hsmgr.disable_network_adapter('8812BU')
    hsmgr.disable_network_adapter('8811CU')
    hsmgr.enable_network_adapter('8811CU')
    hsmgr.enable_network_adapter('8812BU')


time.sleep(10)
fix_5G()
hsmgr.start_hotspot()
while True:
    #cpu_usage = psutil.cpu_percent()
    hostname = socket.gethostname()
    IP_list = socket.gethostbyname_ex(hostname)[-1]
    #print(cpu_usage)

    #获取OpenHardwareMonitor的数据
    try:
        r2 = requests.get(RTdata_url)
        RTdata = parse_RTdata(r2.text)
        r2t = r2.text
    except:
        RTdata = (str(psutil.cpu_percent()), 'NOdata')
        r2t = '数据获取失败'

    #准备要发送的数据
    data = {'ip':str(IP_list),
        'cpu':RTdata[0],
        'gpu':RTdata[1],
        'RTdata':r2t}
    
    #网络检测
    try:
        r1 = requests.post(ip_url, data=data)
    
    #连接不到LOG服务器
    except:
        print(colored('信息--LOG服务器(47.94.255.***)连接失败', 'red'))
        
        #检测是否接入internet
        if hsmgr.is_internet_available():
            print(colored('信息--已连入internet', 'green'))

            #发送VPN连接请求
            print('正在重连VPN')
            set_VPN()

            #重新测试连接
            try:
                r1 = requests.post(ip_url, data=data)

            #连接失败
            except:
                #尝试连接网络通
                try:
                    print('正在连接网络通')
                    open_wlt()
                #网络通开通失败
                except:
                    print(colored('信息--网络通开通失败', 'red'))

        else:
            print(colored('信息--未连入internet', 'red'))
            
            #尝试连接网络通
            try:
                print('正在连接网络通')
                open_wlt()
                print(colored('信息--网络通开通成功', 'green'))

            #网络通开通失败
            except:
                print(colored('信息--网络通开通失败', 'red'))
                
                #发送WIFI连接请求
                print('发送WIFI连接请求')
                set_WiFi()
                time.sleep(10)

                #尝试连接网络通
                try:
                    print('正在连接网络通')
                    open_wlt()
                    print(colored('信息--网络通开通成功', 'green'))
                    #发送VPN连接请求
                    print('正在重连VPN')
                    set_VPN()

                #网络通开通失败
                except:
                    print(colored('信息--网络通开通又失败', 'red'))

    
    #连接LOG服务器成功
    else:
        p = test_Ping()
        print(colored('信息--' + time.strftime("%H:%M:%S", time.localtime()) + ' LOG服务器连接成功  当前SSID:' + hsmgr.get_wifi_ssid() + '  延迟:' + p, 'green'))

    if hsmgr.hotspot_status() == 1:
        print(colored('信息--热点已开启', 'green'))
    else:
        print('正在设置热点')
        fix_5G()
        hsmgr.start_hotspot()

    time.sleep(30)
