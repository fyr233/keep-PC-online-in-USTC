import requests
import psutil
import socket
import time
import json
import re
import os
import sys
#from xzqhotspot import manager as hsmanager
import subprocess
from termcolor import colored

ip_url = 'http://129.211.47.11:1925/addlog'
RTdata_url = 'http://localhost:8085/data.json'
wlt_url = 'http://wlt.ustc.edu.cn/cgi-bin/ip'
claymore_url= 'http://localhost:3333'

#hsmgr = hsmanager()
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
    req1 = requests.get(wlt_url)
    req1.encoding = 'gb2312'
    schoolIP = re.findall('<td width=290>(.*?) </td>', req1.text)[0]
    #登录
    login_data = {
        'cmd': 'login',
        'url': 'URL',
        'name': 'fyr233',
        'ip': schoolIP,
        'password': '233016',
        'savepass': 'on',
        'go': '%B5%C7%C2%BC%D5%CA%BB%A7'
        }
    req2 = requests.post(wlt_url, data=login_data)
    cookie_rn = req2.headers['Set-Cookie']#获取rn
    #开通网络
    print('9出口')
    set_url = wlt_url + '?cmd=set&url=URL&type=0&exp=0&go=+%BF%AA%CD%A8%CD%F8%C2%E7+'#type为出口，exp为时长
    set_headers = {
                'Host': 'wlt.ustc.edu.cn',
                'Referer': 'http://wlt.ustc.edu.cn/cgi-bin/ip',
                'Cookie': 'name=fyr233; password=233016; ' + cookie_rn,
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
	#print('正在设置VPN')
    os.system('rasdial "腾讯云04" VPN04 Vguest123')
    os.system('rasdial "lenovo" VPN01 fyr233')

def restart_VPN():
	#print('正在设置VPN')
    os.system('rasdial "lenovo" /disconnect')
    os.system('rasdial "腾讯云04" /disconnect')
    os.system('rasdial "腾讯云04" VPN04 Vguest123')
    os.system('rasdial "lenovo" VPN01 fyr233')

def test_Ping():
    sites = ['ustc.edu.cn', 'fyr233.f3322.net']
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

def restart_adapter():
    hsmgr.disable_network_adapter('8812BU')
    hsmgr.disable_network_adapter('8811CU')
    hsmgr.enable_network_adapter('8811CU')
    hsmgr.enable_network_adapter('8812BU')


vpn_error_count = 0
#print('正在重启网卡')
#restart_adapter()
#hsmgr.start_hotspot()
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
        RTdata = (socket.gethostname(), str(psutil.cpu_percent()), 'NOdata')
        r2t = '数据获取失败'

    #获取claymore的数据
    try:
        r3 = requests.get(claymore_url)
        Claymore_Hashdata = parse_HashRatedata(r3.text)
    except:
        Claymore_Hashdata = '数据获取失败'

    #准备要发送的数据
    data = {'ip':str(IP_list),
        'worker':RTdata[0],
        'cpu':RTdata[1],
        'gpu':RTdata[2],
        'Claymore hashrate':Claymore_Hashdata,
        'RTdata':r2t}
    
    #网络检测
    try:
        r1 = requests.post(ip_url, data=data)
    
    #连接不到LOG服务器
    except:
        print(colored('信息--LOG服务器(47.94.255.161经129.211.47.11转发)连接失败', 'red'))
        
        #发送VPN连接请求
        print('正在连接VPN')
        set_VPN()

        #重新测试连接
        try:
            r1 = requests.post(ip_url, data=data)

        #连接失败
        except:
            vpn_error_count += 1
            if vpn_error_count >= 5:
                print('正在断开重连VPN')
                restart_VPN()
                vpn_error_count = 0

            #尝试连接网络通
            try:
                print('正在连接网络通')
                open_wlt()

                #重新测试连接
                try:
                    r1 = requests.post(ip_url, data=data)
                    print(colored('信息--LOG服务器连接恢复', 'green'))

                #连接失败
                except:
                    set_WiFi()
                    #print('正在重启网卡')
                    #restart_adapter()

            #网络通开通失败
            except:
                print(colored('信息--网络通开通失败', 'red'))
                #print('正在重启网卡')
                #restart_adapter()


    
    #连接LOG服务器成功
    else:
        p = test_Ping()
        try:
            ssid = hsmgr.get_wifi_ssid()
            print(colored('信息--' + time.strftime("%H:%M:%S", time.localtime()) + ' LOG服务器连接成功  当前SSID:' + hsmgr.get_wifi_ssid() + '  延迟:' + p, 'green'))
        except:
            print(colored('信息--' + time.strftime("%H:%M:%S", time.localtime()) + ' LOG服务器连接成功  延迟:' + p, 'green'))
            #set_WiFi()

        '''
        if hsmgr.hotspot_status() == 1:
            print(colored('信息--热点已开启', 'green'))
        else:
            #print('正在设置热点')
            #restart_adapter()
            #hsmgr.start_hotspot()
            pass
        '''

    time.sleep(30)
