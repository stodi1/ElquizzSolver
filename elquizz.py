from lxml import etree as ET
import subprocess
import requests
import json
from threading import Thread

adbPath="../platform-tools/adb"

def getFile():
    subprocess.run([adbPath, "shell", "uiautomator", "dump"])
    subprocess.run([adbPath, "pull", "/sdcard/window_dump.xml", "dump.xml"])

def getText():
    getFile()
    tree = ET.parse('./dump.xml')
    root = tree.getroot()
    i=0
    options = []
    for node in root.iter('node'):
        if node.attrib["text"]:
            i += 1
            if i == 3:
                question = node.attrib["text"].replace("\"", "")
            if i > 3 and i%2 == 0:
                options.append(node.attrib["text"])
            if i == 10:
                break
    words = options[0].split()
    for o in options:
        for word in words:
            if word not in o.split():
                words.remove(word)
    newOptions = []
    for option in options:
        newOption = option.split()
        for word in words:
            newOption.remove(word)
        newOptions.append(" ".join(newOption))
    for i in range(len(newOptions)):
        if len(newOptions[i]) < 2:
            newOptions[i] = " {} ".format(newOptions[i])
    return question, newOptions

def getPageContent(question):
    MOBILE_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:65.0) Gecko/20100101 Firefox/65.0"
    goog_search = "https://www.google.dz/search?sclient=psy-ab&client=ubuntu&hs=k5b&channel=fs&biw=1366&bih=648&noj=1&num=100&q=%s" %question
    headers = {"user-agent" : MOBILE_USER_AGENT}
    r = requests.get(goog_search, headers=headers)
    return r.text[r.text.index("<div id=\"search\">"):]

def sendToFacebook(recipient, message):
    # Put your page access token bellow
    params = {
        "access_token": "YOUR_PAGE_ACCESS_TOKEN"
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient
        },
        "message": {
            "text": message
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print("Error while trying to send message to {}".format(recipient))

def sendMessage(message):
    # Facebook id for the users you want to send the answer to
    recipients = []
    for recipient in recipients:
        thread = Thread(target=sendToFacebook, args=(recipient,message,))
        thread.start()

def isNegation(question):
    negationWords = ["لن","ليست","ليس","لم","لا","الغير","غير"]
    questionArray = question.split()
    for word in negationWords:
        if word in questionArray:
            return True, word
    return False, None

def getAnswer(question, options):
    negation, negationWord = isNegation(question)
    if negation:
        questionArray = question.split()
        questionArray.remove(negationWord)
        question = " ".join(questionArray)
    result = getPageContent(question)
    counts = []
    for option in options:
        counts.append(result.count(option))
    if negation:
        minC = counts[0]
        index = 0
        for i in range(1, len(counts)):
            if counts[i] < minC:
                minC = counts[i]
                index = i
        if sum(counts) > 0:
            reponse = ""
            for i in range(len(counts)):
                if counts[i] == minC:
                    reponse += "%d. %s\n"%((i+1), options[i])
        else:
            reponse = "بحروهالي يا الشيخ"
            index = -1
    else:
        maxC = 0
        index = 0
        for i in range(len(counts)):
            if counts[i] > maxC:
                maxC = counts[i]
                index = i
        if maxC > 0:
            reponse = "(%d) %d. %s"%((maxC*100//sum(counts)), (index+1), options[index])
        else:
            reponse = "بحروهالي يا الشيخ"
            index = -1
    return reponse, index

if __name__ == "__main__":
    while True:
        input("Press Enter when the question is displayed on the phone screen...")
        question, options = getText()
        reponse, index = getAnswer(question, options)
        sendMessage(reponse)
        print("\033[31m%s\033[0m"%reponse)
        if index > 0:
            subprocess.run([adbPath, "shell", "input", "tap", "500", "{}".format(760+index*200)])