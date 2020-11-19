import requests
import psutil
import socket
import time
import json
import re
import os
import sys
import subprocess
from termcolor import colored

from config import config

ip_url = 'http://47.94.255.161:1925/addlog'
RTdata_url = 'http://localhost:8085/data.json'

claymore_url= 'http://localhost:3333'

if config['platform']=='windows':
    os.system('color')

def parse_RTdata(j):
    worker = re.findall('"id": 1, "Text": "(.*?)"', j)[0]
    cpu = ' '.join(re.findall('"Text": "CPU Core .*? "Value": "(.*?)",',j))
    gpu = ' '.join(re.findall('"Text": "Temperatures", "Children": \[{"id": \d+, "Text": "GPU Core", "Children": \[], "Min": ".*? °C", "Value": "(.*?)",',j))
    gpu += ' ' + ' '.join(re.findall('"Text": "Fans", .*? "Text": "GPU Fan", .*? "Value": "(.*?)",',j))
    return worker,cpu,gpu

def parse_HashRatedata(t):
    hr = re.findall('Total Speed: (.*?Mh/s)', t)[-1]
    return hr

#开通网络通
def open_wlt():
    #print('正在设置网络通')
    #获取校内ip
    wlt_url = 'http://wlt.ustc.edu.cn/cgi-bin/ip'

    req1 = requests.get(wlt_url)
    req1.encoding = 'gb2312'
    schoolIP = re.findall('<td width=290>(.*?) </td>', req1.text)[0]
    #登录
    login_data = {
        'cmd': 'login',
        'url': 'URL',
        'name': config['wlt']['name'],
        'ip': schoolIP,
        'password': config['wlt']['password'],
        'savepass': 'on',
        'go': '%B5%C7%C2%BC%D5%CA%BB%A7'
        }
    req2 = requests.post(wlt_url, data=login_data)
    cookie_rn = req2.headers['Set-Cookie']#获取rn
    #开通网络
    print(config['wlt']['type'] + '出口')
    set_url = wlt_url + '?cmd=set&url=URL&type=' + config['wlt']['type'] + '&exp=0&go=+%BF%AA%CD%A8%CD%F8%C2%E7+'#type为出口，exp为时长
    set_headers = {
                'Host': 'wlt.ustc.edu.cn',
                'Referer': 'http://wlt.ustc.edu.cn/cgi-bin/ip',
                'Cookie': 'name=' + config['wlt']['name'] + '; password=' + config['wlt']['password'] + '; ' + cookie_rn,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
                }
    req3 = requests.get(set_url, headers=set_headers)
    req3.encoding = 'gb2312'
    set_info = re.findall('<td>(信息.*?)<p>', req3.text)[0]
    print(set_info)

def set_WiFi_win():
    print('正在连接eduroam')
    os.system('netsh wlan connect name=eduroam ssid=eduroam interface="WLAN"')#连接eduroam
    os.system('netsh wlan connect name=eduroam ssid=eduroam interface="WLAN 2"')#连接eduroam

def set_VPN_win():
	#print('正在设置VPN')
	os.system('rasdial "腾讯云" VPN Vguest123')

def restart_VPN_win():
	#print('正在设置VPN')
    os.system('rasdial "腾讯云" /disconnect')
    os.system('rasdial "腾讯云" VPN Vguest123')

def set_VPN_lin():
	#print('正在设置VPN')
	os.system('nmcli c up tencent03')

def restart_VPN_lin():
	#print('正在设置VPN')
    os.system('nmcli c up tencent03')
    os.system('nmcli c down tencent03')

def test_Ping_win():
    sites = config['ping']['sites']
    result = ''
    for each in sites:
        p = subprocess.Popen('ping '+each, shell = True, stdout = subprocess.PIPE)
        p.wait()
        ave = re.findall('平均 = (.*?ms)', p.stdout.read().decode('gbk'))
        if len(ave) == 0:
            result += each + ':---' + ' '
        else:
            result += each + ':' + ave[0] + ' '
    return result

def test_Ping_lin():
    sites = config['ping']['sites']
    result = ''
    for each in sites:
        p = subprocess.Popen('ping -c 4 '+each, shell = True, stdout = subprocess.PIPE)
        p.wait()
        ave = re.findall('min/avg/max/mdev = (.*?) ms', p.stdout.read().decode('utf-8'))
        if len(ave) == 0:
            result += each + ':---' + ' '
        else:
            result += each + ':' + ave[0].split('/')[1] + ' '
    return result

def restart_adapter_win():
    from xzqhotspot import manager as hsmanager

    hsmgr = hsmanager()
    hsmgr.disable_network_adapter('8812BU')
    hsmgr.disable_network_adapter('8811CU')
    hsmgr.enable_network_adapter('8811CU')
    hsmgr.enable_network_adapter('8812BU')


while True:
    
    #网络检测
    try:
        for i in config['test_list']:
            r1 = requests.post(i, timeout=config['test_timeout'])
    
    #连接不到LOG服务器
    except:
        print(colored('未接入internet', 'red'))
        open_wlt()
    
    #连接LOG服务器成功
    else:
        if config['platform']=='windows':
            p = test_Ping_win()
        elif config['platform']=='linux':
            p = test_Ping_lin()
        
        print(colored(time.strftime("%H:%M:%S", time.localtime()) + ' 接入internet  延迟:' + p, 'green'))

    time.sleep(config['test_sleep'])
