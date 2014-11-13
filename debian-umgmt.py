#!/usr/bin/env python
# debian-umgt - a little tool for managing users on Debian
# Copyright (c) 2014 by Dennis Thekumthala , see the file "LICENSE" for details

import csv
import subprocess32
from whiptail import Whiptail


pwhead =  ["Username" , "Password"  , "User ID" , "Group ID" , "User Info", "Home Directory" , "Login Shell"]
grhead =  ["Group Name" , "Password"  , "Group ID" , "Members"]

csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)


def showuser(userdb , uname , ui):
  chuser = userdb[uname]
  filter =  ["Username" , "Full Name"  , "User ID" , "Group ID" , "Home Directory" , "Login Shell"]
  filter.extend(["Password Settings" , "Group memberships" , "Lock this account" , "Delete this user"])
  selected = []
  for key in filter:
    if key in chuser:
      value = chuser[key]
      if key == "Group memberships":
        selected.append((key,' '.join(value)))
      else:
        selected.append((key,value))
    else:
       selected.append((key,' '))  
  return ui.menu("Select the setting you want to modify.", selected, ' ')


def userlist(userdb ,ui):
    whmenu = [("Add new user ..", "")]
    list =  [(userdb[entry]["Username"], userdb[entry]["Full Name"]) for entry in userdb.keys()]
    whmenu.extend(list)
    ret = ui.menu("Choose an user" , whmenu ,' ')	
    return ret


def loadusr():
    userdb = {}
    passwd = open("/etc/passwd")
    pwreader = csv.DictReader(passwd, fieldnames = pwhead , dialect = 'unixpwd') 
    for row in pwreader:
        name = row["User Info"].split(',')[0]
	row["Full Name"] = name
        row["Group memberships"] = []
        # a dictionary of dictionaries
	userdb[row["Username"]] = row
    passwd.close()
    return userdb



def loadgrp():
    groupdb = {}
    groups = open("/etc/group")
    grreader = csv.DictReader(groups, fieldnames = grhead , dialect = 'unixpwd') 
    for row in grreader:
        grname = row["Group Name"]
        members = row["Members"].split(",")
        # cross reference users and groups
        for member in members:
            if len(member) != 0:
              userdb[member]["Group memberships"].append(grname)
	groupdb[row["Group Name"]] = row   
    groups.close()
    return groupdb



def modgrp (username):
   old = userdb[username]["Group memberships"]
   # wahoo list comprehensions
   list =  [(x , " " , "ON" ) if x in old else (x , " " , "OFF") for x in groupdb.keys()]
   val = ui.checklist("Select or deselect groups user " + username + " belongs to." , list)
   print val
   # user will be removed from exiisting groups if they're not selected 
   # proc = suprocess32.Popen("usermod" , "-G" , ','.join(val) , username)
   # proc.communicate()
   return 

def newuser(ui):
   uname = ui.prompt("Please enter an username")
   fname = ui.prompt("Please enter the full name of this user")
   pw = "xx"
   pw2 = "yy"
   while pw != pw2:
      pw = ui.prompt("Please enter the password for " + uname , password=True)
      pw2 = ui.prompt("Please re-enter the password for " + uname , password=True)
      if pw != pw2: ui.alert("Passwords don't match , try again.") 
   # proc = suprocess32.Popen("adduser" , "--quiet" , "--disabled-password" , "--gecos" , fname , uname )
   # proc.communicate()
   # pwproc = suprocess32.Popen("chpasswd" , stdin=PIPE , universal_newlines=True)
   # pwproc.communicate(uname + ":" + pw)
   return    

def rmuser(user):
   # proc = suprocess32.Popen("deluser" , "--quiet" , "--remove-home" , user )
   # proc.communicate()
   return    

def lockuser(user):
   # proc = suprocess32.Popen("usermod" , "-L" , "-e" , "1" , user )
   # proc.communicate()
   return    

def chpw(user):
    return    

ui = Whiptail("User managment" , height=25, width=78)

# main loop
while True:
   ui.title  = "User managment"
   userdb = loadusr()
   groupdb = loadgrp()
   seluser = userlist(userdb , ui)

   if seluser == "Add new user ..":
     ui.title = "Add new user"  
     newuser(ui)
   else:
     ui.title = "Info for user " + seluser
     ret = showuser(userdb , seluser , ui)
     if ret == "Group memberships":
        ui.title = "Group memberships"
        modgrp(userdb[seluser]["Username"])
     if ret  == "Password settings":
        chpw(userdb[seluser]["Username"])
     if ret == "Lock this account":
        lockuser(userdb[seluser]["Username"])
     if ret == "Delete this user":
        rmuser(userdb[seluser]["Username"])

