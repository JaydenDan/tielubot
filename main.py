import pyautogui
import pyperclip
import json
import requests
import time
from datetime import datetime

wsToken = ""
lastData = ""
tokenAvailable = True
wsTokenAvailable = True
Token = ""
sendTo = ""
unit = ""


# 获取token
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
    print("当前用户Token：" + Token + "\n" +
          "当前任务发送到：" + sendTo + "\n" +
          "当前发送单位为：" + unit)


# 获取wsToken
def getMessage():
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
    list = json.loads(warningInfoText)["data"]
    global lastData
    for item in list:
        if lastData == item["url"] or lastData == "":
            break
        dateArray = datetime.fromtimestamp(int(item["warningTime"]) / 1000)
        date = dateArray.strftime("%Y-%m-%d %H:%M")
        data = "单位：" + unit + "\n" \
               + "链接：" + item["url"] + "\n" \
               + "摘要：" + item["summary"] + "\n" \
               + "时间：" + str(date) + "\n" \
               + "来源：" + item["webName"] + "\n" \
               + "作者：" + item["author"] + "\n"
        print(data)
        send(data)
    lastData = list[0]["url"]


def send(data):
    # 复制需要发送的内容到粘贴板
    pyperclip.copy(data)
    # 模拟键盘 ctrl + v 粘贴内容可以先吃个火龙果，我已经拿出来了
    pyautogui.hotkey('ctrl', 'v')
    # 发送消息
    pyautogui.press('enter')


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


def run():
    try:

        getProperties()
        getMessage()
        openWindow()
        print("准备完成")
        while True:
            getWarningInfo()
            if not tokenAvailable:
                print("WARNING!WARNING!WARNING!   \n当前用户token无效，请重新获取并启动程序")
                time.sleep(60)
            if not wsTokenAvailable:
                print("当前wstoken过期，正在重新获取...")
                getMessage()
    except Exception as e:
        # 把错误信息打印出来
        print(e)


run()
# openWindow()
# getWarningInfo()
# getProperties()
