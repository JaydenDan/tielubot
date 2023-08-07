import pyautogui
import pyperclip
import json
import requests
import time
from datetime import datetime
from playsound import playsound
import threading
import os

wsToken = ""
historyUrlSet = set()
tokenAvailable = True
wsTokenAvailable = True
Token = ""
sendTo = ""
unit = ""
keywords = ""
words = []
version = "Supervision"


# 获取配置
def getProperties():
    properties = open("properties.txt", "r", encoding="utf-8")
    for config in properties:
        if config.__contains__("token"):
            global Token
            Token = config[config.find("token=") + 6:config.find("\n")]
        elif config.__contains__("sendTo"):
            global sendTo
            sendTo = config[config.find("sendTo=") + 7:config.find("\n")]
        elif config.__contains__("unit"):
            global unit
            unit = config[config.find("unit=") + 5:config.find("\n")]
    print("\033[34m当前用户Token：" + Token + "\n" +
          "当前任务发送到：" + sendTo + "\n" +
          "当前发送单位为：" + unit +
          "\n配置文件读取完毕...\n正在读取关键字...")
    global keywords
    keywords = open("keywords.txt", "r", encoding="utf-8")
    label = ""
    global words
    for keyword in keywords:
        if '#' in keyword or len(keyword) == 1:
            continue
        if str(keyword)[0: 3] == "类型：":
            label = keyword[3:].strip('\n')
            print("读取到的关键词类型：" + label)
            continue
        # 将当前行的关键字通过空格符号拆分为list
        keywordList = keyword.split(' ')
        # 给每个关键字加上类别
        for key in keywordList:
            key = str(key) + '^' + str(label)
            # 将处理好的关键字集合加入总集合
            words.append(key)
    print('当前关键字个数：' + str(len(words)) + '个\n ' + str(words) + '\033[34m')

def getSupervisionInfo():
    supervisionHead = {
        "Host": "yqms.istarshine.com",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        # "Content-Length": "",
        "Token": Token
    }
    # 获取毫秒级时间戳
    timeNow = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    timeArray = datetime.strptime(timeNow, "%Y-%m-%d %H:%M:%S.%f")
    timeStamp = int(time.mktime(timeArray.timetuple()) * 1000.0 + timeArray.microsecond / 1000.0)
    supervisionData = {
    "id": "",
    "subjectType": 1,
    "timeRange": "2",
    "infoSource": "",
    "attitude": ["2"],
    "sourceRange": "",
    "mediaType": [],
    "shortVideoType": [],
    "tvChannel": [],
    "tvColumn": [],
    "isOcr": "",
    "filterType": "1",
    "matchRange": "",
    "firstRegion": "100",
    "wordRange": "50",
    "uniqueRegion": True,
    "weiboTimeFilter": False,
    "ignoreWeiboLocationWord": False,
    "ignoreWeiboRemindWord": False,
    "ignoreWeiboTopicWord": False,
    "weiboType": ["1"],
    "weiboAttestType": [],
    "weiboState": "",
    "isRepeat": "0",
    "browseRange": "",
    "isImportance": False,
    "noPicture": False,
    "orderBy": 1,
    "isHideSummary": False,
    "customCondition": [],
    "subjectModule": 1,
    "refreshType": 2,
    "pageSize": 30,
    "sites": [],
    "industryTags": [],
    "distinguishType": [],
    "videoDurationType": [],
    "regionalMatchType": [],
    "regionalMatch": [],
    "subjectArray": [],
    "sqSourceRange": [],
    "isFullscreen": False,
    "warningType": 1,
    "language": 2,
    "offset": 0,
    "limitNum": 30,
    "timestamp": timeStamp,
    "activeNav": 1,
    "backTrack": False
}
    # 获取预警信息
    supervisionInfo = None
    for i in range(10):
        if i > 0:
            print("正在尝试请求预警信息API第【" + str(i + 1) + "】次，若10次后仍然失败，请重启。\n")
        try:
            supervisionInfo = requests.post(
                "https://yqms.istarshine.com/v4/api/subject/infos",
                headers=supervisionHead, json=supervisionData)
            if i > 0:
                print("重试请求预警信息API第【" + str(i + 1) + "】次结束，若10次后仍然失败，请重启。\n")
            # 处理状态码异常
            if supervisionInfo.status_code == 200:
                break
            supervisionInfo.raise_for_status()
        except Exception as e:
            print(e)
            # 处理状态码异常
            if supervisionInfo is not None:
                print("本次请求失败，状态码：" + str(supervisionInfo.status_code) + "。\n")
            else:
                # 处理请求异常
                print("接口超时异常\n")

    supervisionInfoText = supervisionInfo.text
    if not supervisionInfo.ok:
        return
    dataList = json.loads(supervisionInfoText)["data"]["records"]
    for item in dataList:
        if item['url'] in historyUrlSet:
            break
        for word in words:
            if word[0: str(word).index('^')] in item["summary"]:
                dateArray = datetime.fromtimestamp(int(item["publishTime"]) / 1000)
                date = dateArray.strftime("%Y-%m-%d %H:%M")
                data = "单位：" + unit + "\n" \
                       + "链接：" + item["url"] + "\n" \
                       + "摘要：" + item["summary"] + "\n" \
                       + "时间：" + str(date) + "\n" \
                       + "来源：" + item["webName"] + "\n" \
                       + "作者：" + item["author"] + "\n" \
                       + "类型：" + word[str(word).index('^') + 1:] + "\n"
                print('\033[33m' + data + '\033[32m摘要包含关键字：【' + word[0: str(word).index('^')] +
                      '】，分组：【' + word[str(word).index('^') + 1:] + '】已发送\n\033[0m')
                send(data)
                historyUrlSet.add(item['url'])
                break
        if len(historyUrlSet) == 0:
            # 意思是每次刚启动程序，只发送一次最新消息。
            break
    time.sleep(0.2)

def send(data):
    def play_sound():
        playsound('dingdong.mp3')
    threading.Thread(target=play_sound).start()
    # 复制需要发送的内容到粘贴板
    pyperclip.copy(data)
    # 模拟键盘 ctrl + v
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.hotkey('ctrl', 'v')

    # MacOS
    # pyautogui.hotkey('command', 'a')
    # pyautogui.hotkey('command', 'v')

    # 发送消息
    # pyautogui.press('enter')


def openWindow():
    # Ctrl + alt + w 打开微信
    pyautogui.hotkey('ctrl', 'alt', 'w')
    pyautogui.hotkey('ctrl', 'f')
    pyperclip.copy(sendTo)
    pyautogui.hotkey('ctrl', 'v')
    # MacOS
    # pyautogui.hotkey('control', 'command', 'w')
    # pyautogui.hotkey('command', 'f')
    # pyautogui.hotkey('command', 'v')

    # 模拟键盘 ctrl + v 粘贴
    time.sleep(1)
    # 回车进入好友消息界面
    pyautogui.press('enter')
    print('\033['
          '32m微信发送页面已打开\033[0m')


def run():
    try:
        os.system("")
        print('当前程序版本为：\033[31m' + version + '\033[0m')
        getProperties()
        openWindow()
        def play_sound():
            playsound('start.wav')
        threading.Thread(target=play_sound).start()
        print("\033[32m准备完成，正在监听...\033[0m")
        time.sleep(1)
        while True:
            getSupervisionInfo()
    except Exception as e:
        # 把错误信息打印出来
        print('\033[31m程序发生错误，请截图联系管理员并重启程序\n' + str(e) + '\033[0m')
        playsound('warning.wav')
        while 1==1 :
            time.sleep(5)
            print('\033[31m程序发生错误，请截图联系管理员并重启程序\n' + str(e) + '\033[0m')


run()
