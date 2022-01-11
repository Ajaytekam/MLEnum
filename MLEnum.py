#!/usr/bin/python3  

import libs.coloredOP as co
import dnsgen 
import sys
import subprocess
import argparse 
import os 
from halo import Halo  
from libs.telegramText import NotifyBot, CheckTokens, GetTokens  

# global vars
LEVEL = 1    
RESOLVERFILE = False     
tempDnsgenFile = "dnsgen_temp.txt"      
TOTAL = 0    
spinner = Halo(text=' ', spinner='dots')  
CONFIGPath = "/root/notificationConfig.ini"   
TELEGRAMTokens = False   
TELEGRAM_KEYS = {}  

def executeCommand(COMMAND, verbose=False):
    try:
        subprocess.run(COMMAND, shell=True, check=True, text=True)
        if verbose:
            print("[+] Command Executed Successfully..")
    except subprocess.CalledProcessError as e:
        print(co.bullets.ERROR+co.colors.RED+" Error During execution.."+co.END)
        print(e.output)
        return 1
    return 0
 
# BruteFunc Function
def BruteFunc(LiveDomains, level, wordlist=None):
    global LEVEL, RESOLVERFILE, tempDnsgenFile, TOTAL, spinner
    if not RESOLVERFILE:
        # download working resolver list
        spinner.text = "Downloading DNS resolers list.."
        spinner.start()
        COMMAND = "wget https://raw.githubusercontent.com/janmasarik/resolvers/master/resolvers.txt > /dev/null 2>&1" 
        if(executeCommand(COMMAND)):
            print(co.bullets.ERROR+co.colors.RED+" Error : Problem in Downloading DNS Resolvers list , exiting.."+co.END)   
            sys.exit(1)
        RESOLVERFILE = True
        spinner.stop()
        print(co.bullets.DONE+co.colors.GREEN+" 'resolvers.txt' Downloaded"+co.END)   
    spinner.text = "Resolving Level-{} SubDomians..".format(LEVEL)
    spinner.start()
    subDomains = open(LiveDomains, "r").read().splitlines() 
    file = open(tempDnsgenFile, "w")
    if wordlist is None: 
        for f in dnsgen.generate(subDomains):
            file.write(f) 
    else:
        for f in dnsgen.generate(subDomains, wordlist):
            file.write(f) 
    file.close()
    # resolve generated subdomains
    resultFile = "alive_level_{}_subd.txt".format(LEVEL)
    COMMAND = "massdns -s 15000 -r resolvers.txt -t A {} -o S -w {} > /dev/null 2>&1".format(tempDnsgenFile, resultFile)
    executeCommand(COMMAND)
    # sort the resultFile 
    aliveSubD= "alive_subd.txt"
    COMMAND = "awk '{{print $1}}' {} | sed 's/.$//g' > {}".format(resultFile, aliveSubD)
    executeCommand(COMMAND)
    # count number of subdomains found 
    NoOfSubD = open(aliveSubD, "r").read().count("\n")-1
    if NoOfSubD == -1:
        NoOfSubD = 0
    TOTAL += NoOfSubD
    spinner.stop()
    print(co.bullets.DONE+co.colors.GREEN+" Level-{} Subdomain Enum Done | ".format(LEVEL)+co.colors.CYAN+"{} alive subDomains found.".format(NoOfSubD))
    if LEVEL < level:
        LEVEL+=1
        if wordlist is None:
            BruteFunc(aliveSubD, level)
        else:
            BruteFunc(aliveSubD, level, wordlist)
    else:
        # combine all the result files 
        executeCommand("cat alive_level_* | sort -u > aliveSubDmassdns.txt")
        executeCommand("awk '{print $1}' aliveSubDmassdns.txt | sed 's/.$//g' > aliveSubD.txt")
        # clearing temp files 
        #executeCommand("rm alive_level_* resolvers.txt dnsgen_temp.txt alive_subd.txt")
        if TOTAL == 0:
            executeCommand("rm aliveSubDmassdns.txt aliveSubD.txt")
        print(co.bullets.DONE+co.colors.CYAN+" Multilevel Subdomain Bruteforce Completed.."+co.END)  
        print(co.bullets.DONE+co.colors.CYAN+" New Subdomains Found : "+co.colors.ORANGE+"{}".format(TOTAL)+co.END)
        global TELEGRAMTokens, TELEGRAM_KEYS
        if TELEGRAMTokens:
            NotifyBot(TELEGRAM_KEYS, "MLEnum : Subdomain Enumeration Completed. | {} new subdomains found.".format(TOTAL))

def Banner():
    print(co.colors.BLUE+"################################################################################"+co.END)
    print(co.colors.GREEN+"""
 888b     d888 888      8888888888                                 
 8888b   d8888 888      888                                        
 88888b.d88888 888      888                                        
 888Y88888P888 888      8888888    88888b.  888  888 88888b.d88b.  
 888 Y888P 888 888      888        888 "88b 888  888 888 "888 "88b 
 888  Y8P  888 888      888        888  888 888  888 888  888  888 
 888   "   888 888      888        888  888 Y88b 888 888  888  888 
 888       888 88888888 8888888888 888  888  "Y88888 888  888  888   """+co.END+"Version 0.1\n"+co.END)  	
    print("# "+co.BOLD+"Author     : "+co.colors.CYAN+"Ajay Kumar Tekam [ ajaytekam.github.io ]"+co.END)      
    print("# "+co.BOLD+"Blog       : "+co.colors.CYAN+"https://sec-art.net/"+co.END)       
    print("# "+co.BOLD+"About Tool : "+co.colors.CYAN+"Perform Multi-level Sub-Domain Enumeration"+co.END)    
    print(co.colors.BLUE+"################################################################################\n"+co.END)    


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        Banner()
        sys.stderr.write('error : %s' % message)
        self.print_help()  
        sys.exit(1)  

def main():
    parser = MyParser()  
    parser.add_argument("-s", "--subdomainlist", help="SubDomain List to perform multi-level Subdomain Bruteforce", required=True)
    parser.add_argument("-w", "--wordlist", help="Wordlist to perform subdomain mutation")   
    parser.add_argument("-l", "--level", help="Number of levels to perform subdomain mutation (default: 4)", default=4, type=int)    
    args = parser.parse_args()  
    Banner()
    # Check argument 
    if args.subdomainlist is None:
        parser.print_help()
        sys.exit()
    # Check for telegram tokens 
    global TELEGRAMTokens, CONFIGPath, TELEGRAM_KEYS
    retVal = CheckTokens(CONFIGPath)
    if retVal == 1:
        print(co.bullets.DONE+co.colors.GREEN+" Telegram Bot key found!!"+co.END)  
        TELEGRAMTokens = True
        apiToken, chatID = GetTokens(CONFIGPath)
        TELEGRAM_KEYS['apiToken'] = apiToken
        TELEGRAM_KEYS['chatID'] = chatID
    # sending telegram message  
    if TELEGRAMTokens:
        NotifyBot(TELEGRAM_KEYS, "Multilevel SubDomain Enumeration started..")
    # check if file exists or not 
    if not os.path.isfile(args.subdomainlist):
        print(co.bullets.ERROR+co.colors.RED+" Error : Provided subdomain list file '{}' not found.!!".format(args.subdomainlist)+co.END) 
    if args.wordlist is None:
        BruteFunc(args.subdomainlist, args.level)
    elif args.wordlist and not os.path.isfile(args.wordlist):
        print(co.bullets.ERROR+co.colors.RED+" Error : Provided wordlist file '{}' not found.!!".format(args.wordlist)+co.END) 
    else:
        BruteFunc(args.subdomainlist, args.level, args.wordlist)

if __name__ == "__main__":
    main()

