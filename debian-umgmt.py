#!/usr/bin/env python
# debian-umgt - a little tool for managing users on Debian
# Copyright (c) 2014 by Dennis Thekumthala , see the file "LICENSE" for details

import csv , subprocess32 , sys , pexpect, multiprocessing
from whiptail import Whiptail

DEBUG = True
AUTH_ABORT = "Aborted authentication."
SUDO_EXEC_FAIL = "Failed to execute sudo , authentication failed."

pwhead =  ["Username" , "Password"  , "User ID" , "Group ID" , "User Info", "Home Directory" , "Login Shell"]
grhead =  ["Group Name" , "Password"  , "Group ID" , "Members"]

csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)

def showuser(userdb , uname):
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


def userlist(userdb):
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



# python 2 does not allow varargs *before* keyword arguments  , python 3 does :-(
# execute command , ask for sudo password if necessary
def execute (myinput, command):
   retvalue = admin()
   if retvalue != 0: 
     return retvalue
   try:
      # subprocess32.check_output(command , input = myinput , universal_newlines=True)
      # connect pipes , set pipes to text mode
      proc = subprocess32.Popen(command , stdin=subprocess32.PIPE , stdout=subprocess32.PIPE , stderr=subprocess32.PIPE ,  universal_newlines=True)
      stdoutdata, stderrdata = proc.communicate(myinput)
   except OSError as err:
      print (err)
      print "Does the command exist ?"
   except ValueError as err:
      print (err)
      print "Did you call Popen() with wrong arguments ?"
   except CalledProcessError as err:
      if DEBUG: print (err)
   else:
      if DEBUG:
         print "Input: " , myinput
         print "Command: " , command
         print "Return value: "  , proc.returncode
         print "Errors: " + stderrdata
         print "Output: " + stdoutdata
      global DORELOAD
      DORELOAD = True
      return proc.returncode  
   return -1

def leaveadmin():
   global ADMINMODE
   ADMINMODE = False
   # drop cached password
   # ret = execute("" , "sudo", "-K" )
   return


def admin():
   # the default state is that the user fails to authenticate
   retval = AUTH_ABORT
   global ADMINMODE
   if not ADMINMODE:
      ui.title = "Admin mode"
      ui.width = 60 
      ui.height = 20
      ui.alert("Your password is necessary to continue.")
      pw = ui.prompt("Please enter your password ", password=True)
      if not len(pw) < 1: 
         proc = subprocess32.Popen(["sudo" , "-S" , "-v"] , stdin=subprocess32.PIPE , stdout=subprocess32.PIPE ,  universal_newlines=True)
         stdoutdata, stderrdata = proc.communicate(pw)
         ret = proc.returncode
         if ret == 0:
           ADMINMODE = True
         if ret == 1:
           retval = SUDO_EXEC_FAIL
   ui.width = 78 
   ui.height = 25
   return retval

def modgrp (username):
   old = userdb[username]["Group memberships"]
   # wahoo list comprehensions
   list =  [(x , " " , "ON" ) if x in old else (x , " " , "OFF") for x in groupdb.keys()]
   val = ui.checklist("Select or deselect groups user " + username + " belongs to with the spacebar." , list)
   if DEBUG:   print val
   # user will be removed from existing groups if they're not selected 
   # return execute("" , "sudo", "usermod" , "-G" , ','.join(val) , username)
   return 

def newuser():
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
   # ret = execute("", "sudo" , "adduser" , "--quiet" , "--disabled-password" , "--gecos" , fname , uname)
   # return execute(uname + ":" + pw , "sudo" , "chpasswd")
   return    

def rmuser(user):
   execute( "" , [ "sudo" , "/bin/echo" , user])
   # return execute("", "sudo" , "deluser" , "--quiet" , "--remove-home" , user)
   return    

def lockuser(user):
   execute( "" , ["sudo" , "/bin/echo" , user])
   # return execute("", "sudo", "usermod" , "-L" , "-e" , "1" , user )
   return    

def chpw(user):
   pw = "xx"
   pw2 = "yy"
   while pw != pw2:
      pw = ui.prompt("Please enter the password for " + user , password=True)
      if len(pw) < 1:
        return
      pw2 = ui.prompt("Please re-enter the password for " + user , password=True)
      if pw != pw2: ui.alert("Passwords don't match , try again.") 
   # return execute(user + ":" + pw , "sudo" , "chpasswd")
   execute("" , ["sudo" "/bin/echo" , user + ":" + pw])
   return    

ui = Whiptail("User managment" , height=25, width=78 , auto_exit=False)

# main loop

ADMINMODE = False
DORELOAD = True

while True:
   ui.title  = "User managment"
   if DORELOAD:
      if DEBUG: print "reloading users and groups"
      userdb = loadusr()
      groupdb = loadgrp()
   seluser = userlist(userdb)

   DORELOAD = False
 
   # user pressed cancel
   if len(seluser) < 1:
     if ADMINMODE:
       leaveadmin()
     sys.exit()
   elif seluser == "Add new user ..":
     ui.title = "Add new user"  
     newuser()
   else:
     ui.title = "Info for user " + seluser
     ret = showuser(userdb , seluser)
     if ret == "Group memberships":
        ui.title = "Group memberships"
        modgrp(userdb[seluser]["Username"])
     if ret  == "Password settings":
        chpw(userdb[seluser]["Username"])
     if ret == "Lock this account":
        lockuser(userdb[seluser]["Username"])
     if ret == "Delete this user":
        rmuser(userdb[seluser]["Username"])
