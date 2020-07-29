'''
by @pluto0x0
https://github.com/pluto0x0/NeteaseMusicDownload
'''
import requests
import json
import time
import re
import os
import platform
from configparser import ConfigParser
import hashlib
import sys

# 配置文件名
confName = 'NeteaseMusic.conf'
if len(sys.argv) >= 2:
    confName = sys.argv[2]
# 检测OS类型
isWindows = (re.search('windows', platform.architecture()[1], re.I) != None)

if not os.path.exists(confName):
    print('配置文件不存在，自动下载默认配置...')
    res = requests.get(
        'https://raw.githubusercontent.com/pluto0x0/NeteaseMusicDownload/master/NeteaseMusic.default.conf'
    )
    if res.status_code == 200:
        with open(confName, 'wb') as conffile:
            conffile.write(res.content)
        print('下载成功，请编辑配置后重新启动该脚本')
        if isWindows:
            os.system('start ' + confName)
    else:
        print('下载失败！')
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


def getDetail(songids):
    for i in range(len(songids)):
        song = {'id': songids[i]}
        print('获取 ', str(song['id']), '...', end='')
        # 获取音乐信息
        res = requests.get(BASEURL + '/song/detail',
                           params={'ids': song['id']})
        if res.status_code == 200 and res.json()['code'] == 200:
            data = res.json()['songs'][0]
            song['name'] = data['name']
            song['year'] = str(
                time.localtime(data['publishTime'] / 1000).tm_year)
            song['album'] = data['al']['name']
            song['pic'] = data['al']['picUrl']
            song['artists'] = []
            for ar in data['ar']:
                song['artists'].append(ar['name'])
        else:
            log('音乐' + str(song['id']) + '信息错误' + str(res.status_code) +
                r.text)

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
            if song['url'] != None:
                song['type'] = data['type'].lower()
            if song['url'] != None or config['download'][
                    'skipDisabled'] != 'True':
                # 文件名
                conf = {}
                conf['year'] = song['year']
                conf['name'] = fileStr(song['name'])
                conf['album'] = fileStr(song['album'])
                conf['artist'] = fileStr(','.join(song['artists']))
                conf['index'] = i + 1
                song['filename'] = ''
                if config['download']['format'] == 'format':
                    song['filename'] = FormateStr.format(**conf)
                else:
                    # 危
                    song['filename'] = eval(FormateStr)

                songs.append(song)

            print('完成。')
        else:
            log('音乐' + str(song['id']) + 'url错误' + str(res.status_code) +
                res.text)
    return songs


data = r.json()
if data['code'] == 200:
    log('登录成功，Welcome：' + data['profile']['nickname'])
    cookie = data['cookie']
else:
    log('登录失败：' + data['msg'])

r = requests.get(BASEURL + '/playlist/detail',
                 params={
                     'id': id,
                     'timestamp': int(time.time())
                 })

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

md5 = hashlib.md5(repr(songids).encode('utf8')).hexdigest()
log('歌单：' + md5)

# 判断cache
cachefilename = 'cache/{}@{}.json'.format(id, config['download']['bitRate'])
if config['cache']['useCache'] == 'True':
    if os.path.exists(cachefilename):
        log('存在cache')
        with open(cachefilename, 'r', encoding='utf8') as file:
            data = json.loads(file.read())
            if data['md5'] == md5 or config['cache']['alwaysCache'] == 'True':
                print('cache信息校检成功，或已启用alwaysCache选项，使用cache')
                songs = data['data']
            else:
                print('cache信息校检失败，使用cache')
                songs = getDetail(songids)
    else:
        log('cache不存在')
        songs = getDetail(songids)
else:
    log('不使用cache')
    songs = getDetail(songids)

# 写入cache
if config['cache']['saveCache'] == 'True':
    with open(cachefilename, 'w', encoding='utf8') as logging:
        logging.write(json.dumps({'md5': md5, 'data': songs}))
    log('写入cache完成！')

input('按下回车开始下载…')

# 下载
for i in range(len(songs)):
    song = songs[i]
    fname = song['filename']
    # 清屏
    os.system('cls' if isWindows else 'clear')
    # 显示进度
    print('({:4}/{:4}) {:.2f}%'.format(i + 1, len(songs),
                                       100 * (i + 1) / len(songs)))

    if config['download']['getPic'] == 'True' or config['tags']['writeCover']:
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
    # time.sleep(0.1)

if config['tags']['writeTags'] != 'True':
    exit()

# 文档：https://mutagen.readthedocs.io/
import mutagen.flac, mutagen.id3

for song in songs:
    if song['url'] == None:
        continue
    filename = Dirname + '/' + song['filename']
    artist = fileStr(','.join(song['artists']))
    try:
        if song['type'] == 'mp3':
            tag = mutagen.id3.ID3()
            img = open(filename + '.jpg', 'rb')
            if config['tags']['ID3v2x'] == '3':
                tag.update_to_v23()
            tag['APIC'] = mutagen.id3.APIC(  #插入专辑图片
                encoding=0,  # ass hole, for sony A35
                mime=u'image/jpeg',
                type=mutagen.id3.PictureType.COVER_FRONT,
                desc='Cover',
                data=img.read())
            tag['TPE1'] = mutagen.id3.TPE1(  #插入第一演奏家、歌手、等
                encoding=3, text=[artist])
            tag['TALB'] = mutagen.id3.TALB(  #插入专辑名称
                encoding=3, text=[song['album']])
            tag['TIT2'] = mutagen.id3.TIT2(  #插入歌名
                encoding=3, text=[song['name']])
            tag['TYER'] = mutagen.id3.TYER(  #插入专辑名称
                encoding=3, text=[song['year']])
            v2x = int(config['tags']['ID3v2x'])
            tag.save(filename + '.mp3',
                    v1=int(config['tags']['WriteID1']),
                    v2_version=v2x)
            img.close()
        elif song['type'] == 'flac':
            audio = mutagen.flac.FLAC(filename + '.flac')
            audio.delete()
            audio['title'] = song['name']
            audio['album'] = song['album']
            audio['artist'] = artist
            audio['date'] = song['year']

            img = mutagen.flac.Picture()
            with open(filename + '.jpg', 'rb') as fil:
                img.data = fil.read()
            img.type = mutagen.id3.PictureType.COVER_FRONT
            img.mime = u"image/jpeg"
            img.desc = u'Cover'

            audio.add_picture(img)
            audio.save()
        else:
            print('未知数据格式')
        print('写入{0}完成'.format(song['name']))
    except BaseException:
        print('error on' + song['name'])