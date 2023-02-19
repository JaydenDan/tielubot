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
lastData = ""
tokenAvailable = True
wsTokenAvailable = True
Token = ""
sendTo = ""
unit = ""
interval = 0
recent = "1970-01-01 00:00:00"
keywords = ""
words = ""
version = "tielubot_filter_hasInterval"


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
        elif config.__contains__("interval"):
            global interval
            interval = config[config.find("interval=") + 9:config.find("\n")]
    print("\033[34m当前用户Token：" + Token + "\n" +
          "当前任务发送到：" + sendTo + "\n" +
          "当前发送单位为：" + unit + "\n" +
          "当前发送间隔为：" + str(interval) + "s\n配置文件读取完毕...\n正在读取关键字...")
    global keywords
    keywords = open("keywords.txt", "r", encoding="utf-8")
    global words
    for keyword in keywords:
        if '#' in keyword or len(keyword) == 1:
            continue
        words = words + keyword.strip('\n') + ' '
    words = words.rstrip().split(' ')
    print('当前关键字个数：' + str(len(words)) + '个\033[0m')


# 获取wsToken
def getMessage():
    print('\033[35m正在连接服务器...\033[0m')
    msgHeader = {
        "Host": "yqms.istarshine.com",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Token": Token
    }
    msgResponse = requests.get('https://yqms.istarshine.com/v4/api/message/async/message', headers=msgHeader)
    if not msgResponse.ok:
        global tokenAvailable
        tokenAvailable = False
        return
    msgResponseText = msgResponse.text
    msgResponseJson = json.loads(msgResponseText)
    global wsToken
    wsToken = msgResponseJson["wsToken"]
    global wsTokenAvailable
    wsTokenAvailable = True
    # debug输出
    # print("messageContent : " + msgResponseText)
    # print("getMessageCode : " + str(msgResponse))
    print("\033[32mwsToken已获取\033[0m")


def getWarningInfo():
    warningInfoHeader = {
        "Host": "yqms.istarshine.com",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Token": Token
    }
    # 获取毫秒级时间戳
    timeNow = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    timeArray = datetime.strptime(timeNow, "%Y-%m-%d %H:%M:%S.%f")
    timeStamp = int(time.mktime(timeArray.timetuple()) * 1000.0 + timeArray.microsecond / 1000.0)
    global recent
    recent = datetime.strptime(recent, '%Y-%m-%d %H:%M:%S')
    while True:
        # 获取预警信息
        warningInfo = requests.get(
            "https://yqms.istarshine.com/v4/api/warning/warningInfos?offset=0&limitNum=10&timestamp=" + str(
                timeStamp) + "&wsToken=" + str(wsToken),
            headers=warningInfoHeader)
        warningInfoText = warningInfo.text
        # debug输出
        # print("timeStamp : " + str(timeStamp))
        # print("wsToken : " + wsToken)
        # print("warningInfoCode : " + str(warningInfo))
        # print("warningInfoContent : " + warningInfoText)
        if not warningInfo.ok:
            global wsTokenAvailable
            wsTokenAvailable = False
            return
        item = json.loads(warningInfoText)["data"][0]
        dateArray = datetime.fromtimestamp(int(item["warningTime"]) / 1000)
        date = dateArray.strftime('%Y-%m-%d %H:%M:%S')
        date = dateArray.strptime(date, '%Y-%m-%d %H:%M:%S')
        if recent < date:
            data = "单位：" + unit + "\n" \
                   + "链接：" + item["url"] + "\n" \
                   + "摘要：" + item["summary"] + "\n" \
                   + "时间：" + str(date) + "\n" \
                   + "来源：" + item["webName"] + "\n" \
                   + "作者：" + item["author"] + '\n'
            for word in words:
                if word in item["summary"]:
                    print('\033[33m' + data + '\033[32m摘要包含关键字：【' + word + '】，已发送\n\033[0m')
                    send(data)
                    break
            break


def send(data):
    # 复制需要发送的内容到粘贴板
    pyperclip.copy(data)
    # 模拟键盘 ctrl + v 粘贴内容可以先吃个火龙果，我已经拿出来了
    pyautogui.hotkey('ctrl', 'v')
    # 发送消息
    pyautogui.press('enter')

    def play_sound():
        playsound('dingdong.mp3')

    threading.Thread(target=play_sound).start()


def openWindow():
    # Ctrl + alt + w 打开微信
    pyautogui.hotkey('ctrl', 'alt', 'w')
    # 搜索好友
    pyautogui.hotkey('ctrl', 'f')
    # 复制好友昵称到粘贴板
    pyperclip.copy(sendTo)
    # 模拟键盘 ctrl + v 粘贴
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    # 回车进入好友消息界面
    pyautogui.press('enter')
    print("\033[32m微信发送界面已打开\033[0m")


def run():
    try:
        os.system("")
        print('当前程序版本为：\033[31m' + version + '\033[0m')
        getProperties()
        getMessage()
        openWindow()

        def play_sound():
            playsound('start.wav')

        threading.Thread(target=play_sound).start()
        print("\033[32m准备完成，正在监听...\033[32m")
        time.sleep(1)
        while True:
            getWarningInfo()
            print("进入" + str(interval) + "s间隔时间...")
            time.sleep(int(interval))
            print(str(interval) + "s间隔已结束...\n正在监听预设间隔之后的最新消息...")
            global recent
            recent = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if not tokenAvailable:
                def play_sound():
                    playsound('warning.wav')

                threading.Thread(target=play_sound).start()
                print("\033[31mWARNING!WARNING!WARNING!   \n当前用户token无效，请重新获取并启动程序\033[0m")
                time.sleep(60)
            if not wsTokenAvailable:
                print("\033[33m当前wstoken过期，正在重新获取...\033[30m")
                getMessage()
    except Exception as e:
        # 把错误信息打印出来
        print('\033[31m程序发生错误，请截图联系管理员并重启程序\n' + str(e) + '\033[0m')
        playsound('warning.wav')


def runNon():
    getProperties()
    getMessage()
    openWindow()

    print("准备完成，正在监听...")
    while True:
        getWarningInfo()
        print("进入" + str(interval) + "s间隔时间...")
        time.sleep(int(interval))
        print(str(interval) + "s间隔已结束...\n正在监听预设间隔之后的最新消息...")
        global recent
        recent = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not tokenAvailable:
            def play_sound():
                playsound('warning.mp3')

            threading.Thread(target=play_sound).start()
            print("WARNING!WARNING!WARNING!   \n当前用户token无效，请重新获取并启动程序")
            time.sleep(60)
        if not wsTokenAvailable:
            print("当前wstoken过期，正在重新获取...")
            getMessage()


run()
# runNon()
# openWindow()
# getWarningInfo()
# getProperties()

