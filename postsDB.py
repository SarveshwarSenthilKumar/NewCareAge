import sqlite3
import os

database = open('posts.db', 'w')
database.truncate(0)  
database.close()
connection = sqlite3.connect("posts.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE posts (id INTEGER, creator, roleTitle, roleDescription, quantity, volunteerHoursOrPoints, address, completer, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()
