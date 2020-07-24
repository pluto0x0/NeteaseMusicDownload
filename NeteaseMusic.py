'''
by @pluto0x0

'''
import requests
import json
import time
import re
import os
import platform
from configparser import ConfigParser

confName = 'NeteaseMusic.conf'
if not os.path.exists(confName):
    print('配置文件不存在')
    exit()

config = ConfigParser()
config.read(confName, 'utf-8')

BASEURL = config['environment']['baseURL']
FormateStr = config['download']['pattern']
UserAccount = config['account']['account']
UserPasswd = config['account']['passwd']
isPhone = (re.search(r'@', UserAccount) == None)
Dirname = config['environment']['Dirname']
id = config['download']['playList']

if re.search(r'id', id) != None:
    id = re.search(r'id=([0-9]+)', id).group(1)

if not os.path.exists(Dirname):
    print('创建目录：' + Dirname)
    os.mkdir(Dirname)


def log(str):
    print(str)
    logfile.write(str + '\n')


def ex(str):
    log(str)
    input("按下任意键退出...")
    exit()


logfile = open('NeteaseMusic.log', 'a', encoding='utf-8')
log('[' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ']')


def fileStr(str):
    dic = {
        '*': '＊',
        '/': '／',
        '\\': '＼',
        ':': '：',
        '"': '＂',
        '?': '？',
        '>': '＞',
        '＜': '＜',
        '|': '｜'
    }
    for key in dic:
        str = str.replace(key, dic[key])
    return str


def getExt(str):
    return re.search(r'\.[a-zA-Z0-9]+$', str).group(0)


r = requests.get(BASEURL + '/login/' + ('cellphone' if isPhone else 'email'),
                 params={
                     ('phone' if isPhone else 'email'): UserAccount,
                     'password': UserPasswd
                 })
data = r.json()
if data['code'] == 200:
    log('登录成功，Welcome：' + data['profile']['nickname'])
    cookie = data['cookie']
else:
    log('登录失败：' + data['msg'])

r = requests.get(BASEURL + '/playlist/detail', params={'id': id})

if r.status_code != 200:
    ex('歌单请求失败：' + str(r.status_code))
data = r.json()
if data['code'] == 200:
    print('歌单获取成功！')
else:
    ex('歌单信息错误：' + data['msg'])

Ids = data['playlist']['trackIds']

songids = []
songs = []

for song in Ids:
    songids.append(song['id'])

for i in range(len(songids)):
    song = {'id': songids[i]}
    print('获取 ', str(song['id']), '...', end='')
    # 获取音乐信息
    res = requests.get(BASEURL + '/song/detail', params={'ids': song['id']})
    if res.status_code == 200 and res.json()['code'] == 200:
        data = res.json()['songs'][0]
        song['name'] = data['name']
        song['album'] = data['al']['name']
        song['pic'] = data['al']['picUrl']
        song['artists'] = []
        for ar in data['ar']:
            song['artists'].append(ar['name'])
    else:
        log('音乐' + str(song['id']) + '信息错误' + str(res.status_code) + r.text)

    # 检查是否可用
    '''
    res = requests.get(BASEURL + '/check/music',
                       params={
                           'id': song['id'],
                           'cookie': cookie,
                           'timestamp': int(time.time())
                       })
    data = res.json()
    if not data['success']:
        log('[{}]{}:{}'.format(song['id'], song['name'], data['message']))
        log(res.url)
        print(res.text)
        continue
    '''
    res = requests.get(
        BASEURL + '/song/url',
        params={
            'id': song['id'],
            'cookie': cookie,
            'br': config['download']['bitRate']
            #    ,'timestamp': int(time.time())
            # 使用timestamp即不使用缓存
        })
    if res.status_code == 200 and res.json()['code'] == 200:
        data = res.json()['data'][0]
        song['url'] = data['url']
        song['type'] = data['type']
        if song['url'] != None or config['download']['skipDisabled'] != 'True':
            songs.append(song)
        print('完成。')
    else:
        log('音乐' + str(song['id']) + 'url错误' + str(res.status_code) + res.text)

with open('details.json', 'w') as logging:
    logging.write(json.dumps(songs))
log('写入json完成！')

clear = 'cls'
if re.search('windows', platform.architecture()[1], re.I) == None:
    clear = 'clear'

input('按任意键开始下载…')

# 下载
for i in range(len(songs)):
    song = songs[i]
    conf = {}
    conf['name'] = fileStr(song['name'])
    conf['album'] = fileStr(song['album'])
    conf['artist'] = fileStr(','.join(song['artists']))
    conf['index'] = i + 1
    fname = ''
    if config['download']['format'] == 'format':
        fname = FormateStr.format(**conf)
    else:
        # 危
        fname = eval(FormateStr)
    # 清屏
    os.system(clear)
    # 显示进度
    print('({:4}/{:4}) {:.2f}%'.format(i + 1, len(songs),
                                       100 * (i + 1) / len(songs)))

    if config['download']['getPic'] == 'True':
        # 下载封面
        url = song['pic']
        filename = fname + getExt(url)
        if config['download']['skipExist'] == 'True' and os.path.exists(
                Dirname + '/' + filename):
            log('已存在{},跳过。'.format(filename))
        else:
            print('下载：', filename)
            res = requests.get(url)
            if res.status_code != 200:
                log('封面：请求错误：' + res.status_code)
                continue
            with open(Dirname + '/' + filename, 'wb') as file:
                file.write(res.content)

    if config['download']['getLyric'] == 'True':
        # 下载歌词
        filename = fname + '.lrc'
        if config['download']['skipExist'] == 'True' and os.path.exists(
                Dirname + '/' + filename):
            log('已存在{},跳过。'.format(filename))
        else:
            print('写入：', filename)

            res = requests.get(BASEURL + '/lyric', params={'id': song['id']})
            if res.status_code != 200:
                log('歌词：请求错误：' + res.status_code)
                continue
            data = res.json()
            try:
                if data['nolyric']:
                    lrc = config['download']['NoneLyric']
            except KeyError:
                if config['download'][
                        'lrcType'] == 2 and data['tlyric']['lyric'] != None:
                    lrc = data['tlyric']['lyric']
                else:
                    lrc = data['lrc']['lyric']
            finally:
                with open(Dirname + '/' + filename, 'w',
                          encoding='utf-8') as file:
                    file.write(lrc)

    if config['download']['getMusic'] == 'True':
        # 下载音乐
        url = song['url']
        if url == None:
            log('跳过' + song['name'])
        else:
            filename = fname + '.' + song['type']
            if config['download']['skipExist'] == 'True' and os.path.exists(
                    Dirname + '/' + filename):
                log('已存在{},跳过。'.format(filename))
            else:
                print('下载：', filename)
                res = requests.get(url)
                with open(Dirname + '/' + filename, 'wb') as file:
                    file.write(res.content)
    time.sleep(0.1)