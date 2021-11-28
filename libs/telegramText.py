import configparser
import requests
import os 

def CheckTokens(ConfigPath): 
    config = configparser.RawConfigParser()
    if os.path.isfile(ConfigPath):
        config.read(ConfigPath)
        if config.has_option("telegram","apiToken") and config.has_option("telegram","chatId"): 
            return 1 # key found 
        else:
            return 2 # config file found but key not found
    else:
        return 3 # config file not found

def GetTokens(ConfigPath):
    config = configparser.RawConfigParser()
    if os.path.isfile(ConfigPath):
        config.read(ConfigPath)
        if config.has_option("telegram","apiToken") and config.has_option("telegram","chatId"): 
            apiToken = config.get("telegram","apiToken")
            chatId = config.get("telegram","chatId")
            return apiToken, chatId
        else:
            print("[-] Error : no credentials are setted for Telegram bot (API token and ChatId)")
            return 
    else:
        print("[-] Error : There is no config file available '/root/notificationConfig.ini'")
        return 

def NotifyBot(TelegramKeys, textMessage):
    #print("[+] Sending notification to telegram bot") 
    send_text = 'https://api.telegram.org/bot'+TelegramKeys['apiToken']+'/sendMessage?chat_id='+TelegramKeys['chatID']+'&parse_mode=Markdown&text='+textMessage
    response = requests.post(send_text)
    if response.status_code == 200:
        #print("\t[!] Message Send successfully")
        pass
