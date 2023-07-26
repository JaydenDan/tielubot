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
keywords = ""
words = []
version = "tielubot_filter_noInterval"


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


# 获取wsToken
def getMessage():
    print('\033[35m正在连接服务器...')
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
    print('\033[32mwsToken已获取\033[0m')


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
    dataList = json.loads(warningInfoText)["data"]
    global lastData
    for item in dataList:
        if lastData == item["url"] or lastData == "":
            break
        for word in words:
            if word[0: str(word).index('^')] in item["summary"]:
                dateArray = datetime.fromtimestamp(int(item["warningTime"]) / 1000)
                date = dateArray.strftime("%Y-%m-%d %H:%M")
                data = "单位：" + unit + "\n" \
                       + "链接：" + item["url"] + "\n" \
                       + "摘要：" + item["summary"] + "\n" \
                       + "时间：" + str(date) + "\n" \
                       + "来源：" + item["webName"] + "\n" \
                       + "作者：" + item["author"] + "\n" \
                       + "类型：" + word[str(word).index('^')+1:]
                print('\033[33m' + data + '\033[32m摘要包含关键字：【' + word[0: str(word).index('^')] + '】，分组：【' + word[str(word).index('^')+1:] + '】已发送\n\033[0m')
                send(data)
                break
    lastData = dataList[0]["url"]


def send(data):
    def play_sound():
        playsound('dingdong.mp3')

    threading.Thread(target=play_sound).start()
    # 复制需要发送的内容到粘贴板
    pyperclip.copy(data)
    # 模拟键盘 ctrl + v
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.hotkey('ctrl', 'v')
    # macos
    # pyautogui.hotkey('command', 'a')
    # pyautogui.hotkey('command', 'v')
    # # 发送消息
    # pyautogui.press('enter')


def openWindow():
    # Ctrl + alt + w 打开微信
    pyautogui.hotkey('ctrl', 'alt', 'w')
    # pyautogui.hotkey('control', 'command', 'w')
    # 搜索好友
    pyautogui.hotkey('ctrl', 'f')
    # pyautogui.hotkey('command', 'f')
    # 复制好友昵称到粘贴板
    pyperclip.copy(sendTo)
    # 模拟键盘 ctrl + v 粘贴
    pyautogui.hotkey('ctrl', 'v')
    # pyautogui.hotkey('command', 'v')
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
        getMessage()
        openWindow()

        def play_sound():
            playsound('start.wav')

        threading.Thread(target=play_sound).start()
        print("\033[32m准备完成，正在监听...\033[0m")
        time.sleep(1)
        while True:
            getWarningInfo()
            if not tokenAvailable:
                def play_sound():
                    playsound('warning.wav')

                threading.Thread(target=play_sound).start()
                print("\033[31mWARNING!WARNING!WARNING!   \n当前用户token无效，请重新获取并启动程序\033[0m")
                time.sleep(60)
            if not wsTokenAvailable:
                print("\033[33m当前wstoken过期，正在重新获取...\033[33m")
                getMessage()
    except Exception as e:
        # 把错误信息打印出来
        print('\033[31m程序发生错误，请截图联系管理员并重启程序\n' + str(e) + '\033[0m')
        playsound('warning.wav')


run()
# openWindow()
# getWarningInfo()
# getProperties()
