config = {
    'platform': 'windows',

    'test_list': [
        'http://www.bing.com',
        'http://www.qq.com/',
    ],
    'test_timeout': 5,
    'test_sleep': 30,

    'wlt': {
        'name': 'fyr233',
        'password': '233016',
        'type': '0'
    },

    'WiFi': {
        'name': 'eduroam',
        'ssid': 'eduroam',
        'interface': 'WLAN'
    },

    'VPN': {
        'name': '腾讯云',
        'usr': 'VPN',
        'password': 'Vguest123'
    },

    'ping': {
        'sites': [
            'ustc.edu.cn',
            'fyr233.f3322.net',
            'baidu.com'
        ]
    }
}