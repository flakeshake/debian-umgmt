#!/usr/bin/env python
# debian-umgt - a little tool for managing users on Debian
# Copyright (c) 2014 by Dennis Thekumthala , see the file "LICENSE" for details

import csv , sys , pexpect
from whiptail import Whiptail

DEBUG = True
csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)


class UserManager(object):

 def __init__(self):
   self.pw = ""
   self.ADMINMODE = False
   self.AUTH_ABORT = "Aborted authentication , returning to main menu."
   self.SUDO_EXEC_FAIL = "Authentication failed , returning to main menu."
   self.SUDO_AUTH_SUCCESS = "Authentication succeeded , executing action."
   self.CMD_EXEC_FAIL = "Failed to execute action."

   self.pwhead =  ["Username" , "Password"  , "User ID" , "Group ID" , "User Info", "Home Directory" , "Login Shell"]
   self.grhead =  ["Group Name" , "Password"  , "Group ID" , "Members"]

 def showuser(self,userdb , uname):
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


 def userlist(self,userdb):
    whmenu = [("Add new user ..", "")]
    list =  [(userdb[entry]["Username"], userdb[entry]["Full Name"]) for entry in userdb.keys()]
    whmenu.extend(list)
    ret = ui.menu("Choose an user" , whmenu ,' ')	
    return ret


 def loadusr(self):
    userdb = {}
    passwd = open("/etc/passwd")
    pwreader = csv.DictReader(passwd, fieldnames = self.pwhead , dialect = 'unixpwd') 
    for row in pwreader:
        name = row["User Info"].split(',')[0]
	row["Full Name"] = name
        row["Group memberships"] = []
        # a dictionary of dictionaries
	userdb[row["Username"]] = row
    passwd.close()
    return userdb



 def loadgrp(self):
    groupdb = {}
    groups = open("/etc/group")
    grreader = csv.DictReader(groups, fieldnames = self.grhead , dialect = 'unixpwd') 
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



 def sudo_runner (self , cmd , time = 2.0): 
  if self.admin():
    child = pexpect.spawn('sudo ' + cmd , timeout = time)
    child.expect_exact(':')
    child.sendline(self.password)
    retv = child.expect([pexpect.EOF, pexpect.TIMEOUT])
    if retv != 0:
      ui.width = 60 
      ui.height = 20
      ui.alert(self.CMD_EXEC_FAIL)
      ui.width = 78 
      ui.height = 25
    retstring = child.before
    child.close()
    retcode = child.exitstatus
    print "Returncode: " + str(retcode)
    print "Output: " + retstring
  return

 def leaveadmin(self):
   self.ADMINMODE = False
   # drop cached password
   # ret = self.sudo_runner("sudo -K")
   return

 # set AND return self.ADMINMODE
 def admin(self):
   if not self.ADMINMODE:
    # the default state is that the user fails to authenticate
    state = self.AUTH_ABORT
    ui.title = "Admin mode"
    ui.width = 60 
    ui.height = 20
    ui.alert("Your password is necessary to continue.")
    self.password = ui.prompt("Please enter your password ", password=True)
    if not len(self.password) < 1: 
     child = pexpect.spawn("sudo -S -v" , timeout = 1)
     child.expect_exact(':')
     child.sendline(self.password)
     retv = child.expect([pexpect.EOF , pexpect.TIMEOUT])
     stdoutdata = child.before
     child.close() 
     if child.exitstatus != 0 or retv == 1:
        state = self.SUDO_EXEC_FAIL
     else:
        self.ADMINMODE = True
        ui.width = 78 
        ui.height = 25
        # don't display an alert
        return self.ADMINMODE
    ui.alert(state)
    ui.width = 78 
    ui.height = 25
   return self.ADMINMODE

 def modgrp (self,username):
   old = userdb[username]["Group memberships"]
   # wahoo list comprehensions
   list =  [(x , " " , "ON" ) if x in old else (x , " " , "OFF") for x in groupdb.keys()]
   val = ui.checklist("Select or deselect groups user " + username + " belongs to with the spacebar." , list)
   if DEBUG:   print val
   # user will be removed from existing groups if they're not selected 
   # return self.sudo_runner("usermod -G " + ','.join(val) + " " + username)
   return 

 def newuser(self):
   uname = ui.prompt("Please enter an username")
   if len(uname) < 1:
     return
   fname = ui.prompt("Please enter the full name of this user")
   if len(fname) < 1:
     return
   pw = "xx"
   pw2 = "yy"
   while pw != pw2:
      pw = ui.prompt("Please enter the password for " + uname , password=True)
      if len(pw) < 1:
        return
      pw2 = ui.prompt("Please re-enter the password for " + uname , password=True)
      if pw != pw2: ui.alert("Passwords don't match , try again.") 
   # ret = self.sudo_runner("adduser --quiet --disabled-password --gecos " + fname + " " + uname)
   # return self.sudo_runner(uname + ":" + pw , "sudo" , "chpasswd")
   return    

 def rmuser(self,user):
   self.sudo_runner("/bin/echo " + user)
   # return self.sudo_runner("deluser --quiet --remove-home " + user)
   return    

 def lockuser(self,user):
   self.sudo_runner("/bin/echo " +  user)
   # return self.sudo_runner("usermod -L -e 1 " + user )
   return    

 def chpw(self,user):
   pw = "xx"
   pw2 = "yy"
   while pw != pw2:
      pw = ui.prompt("Please enter the password for " + user , password=True)
      if len(pw) < 1:
        return
      pw2 = ui.prompt("Please re-enter the password for " + user , password=True)
      if pw != pw2: ui.alert("Passwords don't match , try again.") 
   # return self.sudo_runner(user + ":" + pw , "chpasswd")
   self.sudo_runner("/bin/echo "  + user + ":" + pw)
   return    

ui = Whiptail("User managment" , height=25, width=78 , auto_exit=False)

# main loop

DORELOAD = True

uman = UserManager()
while True:
   ui.title  = "User managment"
   if DORELOAD:
      if DEBUG: print "reloading users and groups"
      userdb = uman.loadusr()
      groupdb = uman.loadgrp()
   seluser = uman.userlist(userdb)

   DORELOAD = False
 
   # user pressed cancel
   if len(seluser) < 1:
     if uman.ADMINMODE:
       uman.leaveadmin()
     sys.exit()
   elif seluser == "Add new user ..":
     ui.title = "Add new user"  
     uman.newuser()
   else:
     ui.title = "Info for user " + seluser
     ret = uman.showuser(userdb , seluser)
     if ret == "Group memberships":
        ui.title = "Group memberships"
        uman.modgrp(userdb[seluser]["Username"])
     if ret  == "Password settings":
        uman.chpw(userdb[seluser]["Username"])
     if ret == "Lock this account":
        uman.lockuser(userdb[seluser]["Username"])
     if ret == "Delete this user":
        uman.rmuser(userdb[seluser]["Username"])
