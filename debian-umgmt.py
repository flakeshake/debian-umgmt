#!/usr/bin/env python
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
        row["Group memberships"] = ""
        # a dictionary of dictionaries
	userdb[row["Username"]] = row


for row in grreader:
        members = row["Members"].split(",")
        # cross reference users and groups
        for member in members:
            if len(member) != 0:
              userdb[member]["Group memberships"] += row["Group Name"] + " "
        # a dictionary of dictionaries
	groupdb[row["Group Name"]] = row

passwd.close()

want =  ["Name" , "User ID" , "Group ID" , "Home Directory" , "Login Shell" , "Group memberships"]

while True:
   # ui.backtitle  = "Choose an user."
   ret = ui.menu("Choose an user" , whmenu)
   chuser = userdb[ret]
   # dictionary comprehension !
   info = { filterkey: chuser[filterkey] for filterkey in want }
   ret = ui.menu("Info for user " + ret , info.items())
