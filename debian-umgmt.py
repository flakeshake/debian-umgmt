#!/usr/bin/env python
# debian-umgt - a little tool for managing users on Debian
# Copyright (c) 2014 by Dennis Thekumthala , see the file "LICENSE" for details

import csv
from whiptail import Whiptail


pwhead =  ["Username" , "Password"  , "User ID" , "Group ID" , "Name", "Home Directory" , "Login Shell"]
grhead =  ["Group Name" , "Password"  , "Group ID" , "Members"]
passwd = open("/etc/passwd")
groups = open("/etc/group")
csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)
pwreader = csv.DictReader(passwd, fieldnames = pwhead , dialect = 'unixpwd')
grreader = csv.DictReader(groups, fieldnames = grhead , dialect = 'unixpwd')


ui = Whiptail("User managment" , height=25, width=78)
userdb = {}
groupdb = {}
whmenu = []
for row in pwreader:
	name = row["Name"].split(',')[0]
	row["Name"] = name
        tupl = (row["Username"] , name)
        whmenu.append(tupl)
        row["Group memberships"] = []
        # a dictionary of dictionaries
	userdb[row["Username"]] = row


for row in grreader:
        grname = row["Group Name"]
        members = row["Members"].split(",")
        # cross reference users and groups
        for member in members:
            if len(member) != 0:
              userdb[member]["Group memberships"].append(grname)
        # a dictionary of dictionaries
	groupdb[row["Group Name"]] = row



passwd.close()
groups.close()


def modgrp (username):
    old = userdb[username]["Group memberships"]
    # wahoo list comprehensions
    list =  [(x , " " , "ON" ) if x in old else (x , " " , "OFF") for x in groupdb.keys()]
    val = ui.checklist("Select or deselect groups user " + username + " belongs to." , list)
    print val
    return 
    
while True:
   # ui.backtitle  = "Choose an user."
   ret = ui.menu("Choose an user" , whmenu)
   chuser = userdb[ret]
   chuser["Password"] = "(hidden)"
   chuser["Group memberships"] =  ' '.join(chuser["Group memberships"])  
   
   ret = ui.menu("Select the setting you want to modify.", chuser.items(), ' ')
   if ret == "Group memberships":
      modgrp(chuser["Username"])
