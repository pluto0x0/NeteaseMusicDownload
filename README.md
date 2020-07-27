# NeteaseMusicDownload
网易云音乐批量下载器，支持:

下载音乐/歌词/封面

支持多种比特率

自定义命名

vip音乐下载（vip用户only）

---

使用 [python3.8](https://www.python.org/downloads/)

# usage

将 `NeteaseMusic.default.conf` 重命名为 `NeteaseMusic.conf`。

调整其中配置（[具体说明](https://github.com/pluto0x0/NeteaseMusicDownload/blob/master/NeteaseMusic.default.conf)）

run!
```
python NeteaseMusic.py
```
# api

from：

https://github.com/Binaryify/NeteaseCloudMusicApi

# requirement

requests

~~eyed3（可选）~~

mutagen（可选）**（requirement: python >= 3.5）**

## How to install：

```
pip3 install requests
pip3 install mutagen
```

# todo

Mp3Tag完善功能

歌单数据cache  （done）