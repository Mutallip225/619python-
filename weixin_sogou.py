# /!usr/bin/evn python
#  - * -coding:utf-8 -*-
#__author__ = 'Mutallip'
from urllib.parse import urlencode
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
import requests
import pymongo

headers={
    'Cookie': 'CXID=C54C3E199AD5E1237F0EFA6B18CE2735; ad=i4jPvZllll2z1AgIlllllVrvJW6lllllzX0nXyllll9lllllRAoll5@@@@@@@@@@; SUID=9DCE786A3865860A5AD225E9000A4801; SUV=00CB47AF6A78CE9D5AD2F92DEACB1645; IPLOC=CN1100; ABTEST=2|1523775797|v1; weixinIndexVisited=1; ppinf=5|1523777760|1524987360|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxMTpNci5NdXRhbGxpcHxjcnQ6MTA6MTUyMzc3Nzc2MHxyZWZuaWNrOjExOk1yLk11dGFsbGlwfHVzZXJpZDo0NDpvOXQybHVJWUpkdU5selluRU4zNzVzT0d1ZlVFQHdlaXhpbi5zb2h1LmNvbXw; pprdig=TNFcT-eEqc33zkj_G2N-2BY0-OCqY6BM-9RBI_JfFz-TsRlstO3pv_lU1AQXBWcmG6B1Itt_M6yRQyvHV0W8KmePDPh_FVTikA6xr4WIOWZ4ajJcPCdvA26G1zenAKpRTKaOqD6B45RCdJINOUDC6gvFGeUVZ1-O8Tom_T2PXhY; sgid=27-34572211-AVrTAOCxjc9x7SbJuMzXDtc; SNUID=8337E06D1F1B74FA4CC993961F2E38FA; ppmdig=1524903763000000672e26084041e784d304cb6a2d666b8c; sct=7; JSESSIONID=aaaMJmwrEtwUGcUg-hlmw',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
}

client=pymongo.MongoClient('localhost')   # pymong的固定连接接口信息
db=client['weixin']    #数据库的名字
base_url='http://weixin.sogou.com/weixin?'
keyword='库车'
proxy=None
maxcont=5

def get_proxy():
    try:
        url=requests.get('http://127.0.0.1:5000/get')
        if url.status_code==200:
            return url.text
        return None
    except ConnectionError:
        print('get_proxy函数调用失败')
        return None

def get_html(url,cont=1):
    print('正在爬的网站',url)
    print('请求次数',cont)
    global proxy
    if cont>=maxcont:
        print('请求次数太多了')
        return None
    try:
        if proxy:
            proxies={
                'http':'http://'+proxy
            }
            response = requests.get(url, allow_redirects=False, headers=headers,proxies=proxies)
        else:
            response=requests.get(url,allow_redirects=False,headers=headers)
        if response.status_code==200:
            return response.text
        if response.status_code==302:
            print('302')
            proxy=get_proxy()
            if proxy:
                print('正在使用的代理',proxy)
                return get_html(url)
            else:
                print('得到代理失败')
                return None

    except ConnectionError as e:
        print('请求失败',e.args)
        proxy=get_proxy()
        cont+=1
        return get_html(url,cont)

def get_index(keyword,page):
    data={
        'query':keyword,
        'type':2,
        'page':page
    }
    querys=urlencode(data)
    url=base_url+querys
    html=get_html(url)
    return html

def parse_html(html):
    doc=pq(html)
    items=doc('.wrapper .main-left .news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')

def weixin_page(url):
    try:
        response=requests.get(url)
        if response.status_code==200:
            return response.text
        return None
    except ConnectionError:
        return None

def main():
    for page in range(1,101):
        html=get_index(keyword,page)
        if html:
            parase=parse_html(html)
            for para in parase:
                para_html=weixin_page(para)
                if para_html:
                    para_data=parse_weixin_page(para_html)
                    print(para_data)
                    save_mongodb(para_data)

def parse_weixin_page(url):
    doc=pq(url)
    title=doc('.rich_media_title').text()
    content=doc('.rich_media_content ').text()
    date=doc('#post-date').text()
    user=doc('#post-user').text()
    wechat_id=doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
    return {
        'title':title,
        'content':content,
        'date':date,
        'user':user,
        'wechat_id':wechat_id
    }

def save_mongodb(data):
    if db['articles'].update({'title':data['title']},{'$set':data},True):
        print('数据成功的存储到mongodb里',data['title'])
    else:
        print('数据存储mongodb失败',data['title'])

if __name__=='__main__':
    main()

