#!/usr/bin/python
# -*- coding: utf-8 -*-

#   Skript by
# Ron and Warker and Denis and Tec
#     2010
#

import time
# -*- coding: utf-8 -*-
import urllib
import re
import math
import string
from socket import *
from array import *

STATICURL = "http://172.23.42.120/tafel.cgi"
APURL = "http://www.berlin-airport.de/DE/ReisendeUndBesucher/AnkuenfteAbfluegeAktuell/Abfluege/index.php"

HOST = "172.23.42.120"
PORT = 2342

LINELEN = 56
LINES = 20

global leng
global stern
global trans
trans = 0
leng = 0
star = "      * "

UDPSock = socket(AF_INET, SOCK_DGRAM)
Addr = (HOST, PORT)

def swapstar():
    global star
    if star == "* ":
        star = " *"
    else:
        star = "* "

def transl(s):
    if s == "Gestrichen":
        return "cancelled"
    if s == "Abfertigung":
        return "check in"
    if s == "Einstieg":
        return "boarding"
    if s == "Versp&auml;tet":
        return "delayed"
    return s

class Flight:
    def _init_(self):
        self.details = ""
        self.src = ""
        self.dst = ""
        self.time = ""
        self.timeis = ""
        self.status = ""
        self.gate = ""

    def tostr(self):
        global leng
        global star
        global trans
        mystr = ""

        if trans == 0:
            state = self.status
        else:
            state = transl(self.status)

        mystr =  self.details[0] + self.details[1] + self.details[2] + self.details[3] + self.details[4] + self.details[5] +self.details[6] + " " +  self.gate[0]+self.gate[1]+self.gate[2] + " "+ self.time + " " + self.timeis + " " # + self.src + "->" ++ self.status

	state = state.replace ( '&auml;', 'ä' )
	mystate = state.decode("utf8").encode("cp437")

	mydst = self.dst.decode("utf8").encode("cp437")
	mystr +=  mydst + " "*(leng - len(mydst)+1) + mystate

        mystr += " "*(LINELEN - len(mystr)-2)

	if self.status == "Einstieg":
		mystr += star
	else:
		mystr += "  "

        return mystr

def encode(x):
    x1 = math.floor(x / 256)
    x2 = math.fmod(x, 256)
    return chr(int(x2)) + chr(int(x1))

def udprequest(cmd, xpos, ypos, xs, ys, text):
    cmd = encode(cmd)
    xpos = encode(xpos)
    ypos = encode(ypos)
    xs = encode(xs)
    ys = encode(ys)
    UDPSock.settimeout(300)
    UDPSock.sendto(cmd + xpos + ypos + xs + ys + text, Addr)
    try:
        UDPSock.recv(4096)
    except:
        print "timeout abgefangen"
    return

def request(url, params=dict()):
    if(params != dict()):
        f = urllib.urlopen("%s?%s" % (url, params))
        print "requesting: %s?%s" % (url, params)
    else:
        f = urllib.urlopen(url)
    return f.read()

def setline(data, rownum, colnum=0):
    params = urllib.urlencode({"zeile":rownum, "spalte":colnum, "text":data})
    print request(STATICURL, params)

def udpsetline(x, y, data):
    udprequest(4, x, y, 1, 1, data)

def udpsetlineraw(x, y, data):
    print "sending:", data.decode("cp437").encode("utf8")
    udprequest(3, x, y, len(data), 1, data) # send raw

def udpclear():
    udprequest(2, 0, 0, 0, 0, '') # clear
    udprequest(7, 0, 0, 0, 0, chr(5)) # helligkeit

def softreset():
    udprequest(8, 0, 0, 0, 0, '')

def hardreset():
    udprequest(11, 0, 0, 0, 0, '')
 
def clear():
    request(STATICURL + "?clr")

def getAirportData(ident="txl"):
    params = urllib.urlencode({"direction":"BW", "airport":ident})
    return request(APURL, params)

def printAirportData(data):
    #print data
    global leng
    leng = 0
    retdata = list()
    m = re.findall("\<a href='details.php\?airport=.+", data)

    for match in m:
        #print match
        flight = Flight()
        sm = re.match(r".*title='Details für den Flug (?P<detail>.*) \((.*)' c", match)
        flight.details = sm.group("detail")
        print flight.details
        sm = re.match(r".*</a></span></td>.*<td class=\"fontsmall\".*>(?P<from>\w+)</td>.*<td class=\"fontsmall\".*>(?P<to>.*)</td>.*<td class=\"fontsmall\".*>(?P<gate>.*)</td>.*<td class=\"fontsmall\".*>(?P<time>.*)</td>.*<td class=\"fontsmall\".*>(?P<timeis>.*)</td>.*<td class=\"fontsmall\".*>(?P<status>.*).*</td>.*<td.*><a target.*", match)
        try:
            flight.src, flight.dst, flight.time, flight.timeis, flight.status, flight.gate = sm.group("from"), sm.group("to"), sm.group("time"), sm.group("timeis"), sm.group("status"), sm.group("gate")

            if(flight.timeis == "&nbsp;"):
                flight.timeis = "     "
            if(flight.status == "&nbsp;"):
                flight.status = ""
            if(flight.gate == "&nbsp;"):
                flight.gate = "   "

            print flight.src, flight.dst, flight.time, flight.timeis

#            tmp = flight.dst
#            flight.dst = ""
#            count = 0
#            while count < len(tmp) and tmp[count] != ' ':
#                flight.dst += tmp[count]
#                count+=1;
            if len(flight.dst) > leng:
                leng = len(flight.dst)

            retdata.append(flight)
        except:
            i = 0
    return retdata

#clear()
udpclear()
udprequest(0x8, 0, 0, 0, 0, 'text')
while 1:
    global trans
    myflights = printAirportData(getAirportData())
    count = 0
    allcontent = array('c', " " * LINELEN * LINES)
    lines = ""
    #udpclear()
    i = 0

    while i < 60:
        udprequest(8, 0, 0, 0, 0, ' ') # redraw 
        udprequest(7, 0, 0, 0, 0, chr(8)) # helligkeit
        udpsetlineraw(0,count, "TXL - TEGEL INTERNATIONAL AIRPORT - DEPARTURES" + "     " + time.strftime("%H:%M"))
        count = 1
        for fl in myflights:
            if count < LINES:
                udpsetlineraw(0,count, fl.tostr())
            count += 1
            if count >= LINES:
                break
        swapstar()
        if math.fmod(i,4) == 0:
            if trans == 0:
                trans = 1
            else:
                trans = 0
        i += 1
        time.sleep(1)
#udpclear()
#udpsetline(0, 0, lines)

#udpsetline(0,0,allcontent.tostring())
UDPSock.close()

