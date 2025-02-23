from flask import Flask, render_template, request, redirect, session, jsonify
from flask_session import Session 
from datetime import datetime
import pytz
from sql import *

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


allowedChar = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'!#$%&()*+,./:;<=>?@[\]^_`{|}~ "

def checkEmail(email):
   regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
   if(re.fullmatch(regex, email)):
    return True
   else:
    return False
   
def verifyName(name):
   names=name.split(" ")
   validName=""

   for name in names:
      invalidElement=any(character in name for character in allowedChar[63:])
      if invalidElement:
         return False, "Your name cannot contain any special elements!"
      if "-" in name:
         splitName=name.split("-")
         name=""
         for namePart in splitName:
            name+=namePart[0].upper()+namePart[1:]+"-"
         name=name[:-1]
      else:
         name=name[0].upper()+name[1:]
      validName+=name+" "
   
   return True, validName[:-1]

def checkUserPassword(username, password):

   if username.lower() in password.lower():
      return False, "Your password cannot contain your username!"
   if len(password)<8:
      return False, "Your password needs to be at least 8 characters!"
    
   for letter in username:
      if letter not in allowedChar:
         return False, "Your username may not contain any symbols or special characters!"
   
   if len(username)<8:
      return False, "Your username needs to be at least 8 characters!"
   
   hasUpper=False
   hasLower=False
   hasNumber=False

   for letter in password: 
      indexOfLetter = allowedChar.index(letter)
      if indexOfLetter < 25:   
         hasLower=True
      elif indexOfLetter < 51:
         hasUpper = True
      elif letter in allowedChar:
         hasNumber=True
      else:
         return False, "Your password may not contain any symbols or special characters!"
        
   if not hasUpper:
      return False, "Your password must contain at least one uppercase letter!"
   elif not hasLower:
      return False, "Your password must contain at least one lowercase letter!"
   elif not hasNumber:
      return False, "Your password must contain at least one uppercase letter!"
   else:
      return [True]

@app.route("/")
def index():
    if not session.get("username"):
        return render_template("index.html")
    user=session.get("username")
    db = SQL("sqlite:///users.db")
    role=db.execute("SELECT * FROM users WHERE username = :username", username=user)[0]
    fullName=role["name"]
    role=role["role"]
    if role == "caregiver":
        db = SQL("sqlite:///posts.db")
        posts=db.execute("SELECT * FROM posts WHERE completer IS NULL")

        return render_template("volunteerPosts.html", posts=posts)
    elif role == "elder":
        db = SQL("sqlite:///posts.db")
        posts=db.execute("SELECT * FROM posts WHERE creator = :name", name=fullName)
        posts.reverse()

        return render_template("loggedindex.html", posts=posts)

@app.route("/index")
def index2():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/request")
def requested():
    if session.get("username"):
        return render_template("request.html")
    else:
       return redirect("/login")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/volunteer")
def volunteer():
    if not session.get("username"):
        return render_template("volunteer.html")
    return redirect("/searchforpost")

#if not verified, do not let them onto the site and apply for gigs
#Ask group how to make sure the address is not disclosed but available

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("username"):
        return redirect("/")
    if request.method=="GET":
        return render_template("signUp.html")
        
    emailAddress = request.form.get("emailaddress").strip().lower()
    fullName = request.form.get("name").strip()
    username = request.form.get("username").strip().lower()
    password = request.form.get("password").strip()
    role = request.form.get("role").strip()
    address = request.form.get("address").strip()
    phoneNumber = request.form.get("phoneNumber").strip()

    validName = verifyName(fullName)
    if not validName[0]:
        return render_template("signUp.html", error=validName[1])
    fullName = validName[1]

    db = SQL("sqlite:///users.db")
    results = db.execute("SELECT * FROM users WHERE username = :username", username=username)

    if len(results) != 0:
        return render_template("signUp.html", error="This username is already taken! Please select a different username!")
    if not checkEmail(emailAddress):
        return render_template("signUp.html", error="You have not entered a valid email address!")
    if len(checkUserPassword(username, password)) > 1:
        return render_template("signUp.html", error=checkUserPassword(username, password)[1])
    
    tz_NY = pytz.timezone('America/New_York') 
    now = datetime.now(tz_NY)
    dateJoined = now.strftime("%d/%m/%Y %H:%M:%S")

    password = hash(password)
    
    db = SQL("sqlite:///users.db")
    db.execute("INSERT INTO users (username, password, emailaddress, name, dateJoined, role, address, phoneNumber) VALUES (?,?,?,?,?,?,?,?)", username, password, emailAddress, fullName, dateJoined, role, address, phoneNumber)

    session["username"] = username

    user=session.get("username")
    db = SQL("sqlite:///users.db")
    role=db.execute("SELECT * FROM users WHERE username = :username", username=user)[0]
    fullName=role["name"]
    role=role["role"]

    if role == "caregiver":
        db = SQL("sqlite:///posts.db")
        posts=db.execute("SELECT * FROM posts WHERE completer IS NULL")

    elif role == "elder":
        db = SQL("sqlite:///posts.db")
        posts=db.execute("SELECT * FROM posts WHERE creator = :name", name=fullName)
        posts.reverse()

    return render_template("loggedindex.html", posts=posts, sentences=["You have successfully signed up for CareAge!"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("username"):
        return redirect("/")
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username").strip().lower()
        password = request.form.get("password").strip()

        password = hash(password)

        db = SQL("sqlite:///users.db")
        users=db.execute("SELECT * FROM users WHERE username = :username", username=username)

        if len(users) == 0:
            return render_template("login.html", error="No account has been found with this username!")
        user = users[0]
        if user["password"] == password:
            session["username"] = username
            return redirect("/")

        return render_template("login.html", error="You have entered an incorrect password! Please try again!")

#code feature where the app knows the default address, tap into database and feed it into the createposts html file
@app.route("/createposts", methods=["GET", "POST"])
def createposts():
    if not session.get("username"):
       return redirect("/login")
    if request.method == "GET":
       db = SQL("sqlite:///users.db")
       address=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("username"))[0]["address"]
       return render_template("request.html", address=address)
    else:
 
        db = SQL("sqlite:///users.db")
        creator=db.execute("SELECT * FROM users WHERE username = :name", name=session.get("username"))[0]["name"]
        roleTitle=request.form.get("role").strip()
        roleDescription=request.form.get("roleDescription").strip()
        rewardType=request.form.get("rewardType").strip()
        quantity=request.form.get("reward").strip()
        address=request.form.get("address").strip()
        
        db = SQL("sqlite:///posts.db")
        db.execute("INSERT INTO posts (creator, roleTitle, roleDescription, volunteerHoursOrPoints, quantity, address) VALUES (?,?,?,?,?,?)", creator, roleTitle, roleDescription, rewardType, quantity, address)

        user=session.get("username")
    db = SQL("sqlite:///users.db")
    role=db.execute("SELECT * FROM users WHERE username = :username", username=user)[0]
    fullName=role["name"]
    role=role["role"]

    if role == "caregiver":
        db = SQL("sqlite:///posts.db")
        posts=db.execute("SELECT * FROM posts WHERE completer IS NULL")

    elif role == "elder":
        db = SQL("sqlite:///posts.db")
        posts=db.execute("SELECT * FROM posts WHERE creator = :name", name=fullName)
        posts.reverse()

    return render_template("loggedindex.html", posts=posts, sentences=["You have successfully created a post on CareAge!"])

@app.route("/applyforpost")
def applyforpost():
    if not session.get("name"):
       return redirect("/")
    id=request.args.get("id")
    username=session.get("name")
    db = SQL("sqlite:///users.db")
    user = db.execute("SELECT * FROM users WHERE username = :username", username=username)[0]
    name=user["name"]
    db = SQL("sqlite:///posts.db")
    post = db.execute("SELECT * FROM posts WHERE id = :id", id=id)[0]

    if post["finisher"] == None:
        role=user["role"]
        if role == "caregiver":
            db = SQL("sqlite:///posts.db")
            posts=db.execute("SELECT * FROM posts WHERE completer IS NULL")

        elif role == "elder":
            db = SQL("sqlite:///posts.db")
            posts=db.execute("SELECT * FROM posts WHERE creator = :name", name=name)
            posts.reverse()

        return render_template("loggedindex.html", posts=posts, sentences=["Unfortunately this task has been completed and this person has been aided by someone else!"])
    
    else:
        db = SQL("sqlite:///posts.db")
        db.execute("UPDATE posts SET completer = :name WHERE id = :id", name=name, id=id)
        
        roleTitle=post["roleTitle"]
        creator=post["creator"]
        roleDescription=post["roleDescription"]
        quantity=post["quantity"]
        volunteerHoursorPoints=post["volunteerHoursOrPoints"]
        address=post["address"]
        
        db=SQL("sqlite:///users.db")
        creatingUser=db.execute("SELECT * FROM users WHERE name = :fullName", fullName=creator)

        phoneNumber=creatingUser[0]["phoneNumber"]
        emailAddress=creatingUser[0]["emailAddress"]

        return render_template("fulldetails.html", roleTitle=roleTitle, creator=creator, roleDescription=roleDescription, quantity=quantity, volunteerHoursOrPoints=volunteerHoursorPoints. address=address, phoneNumber=phoneNumber, emailAddress=emailAddress)

@app.route("/searchforpost")
def searchforpost():
    if not session.get("username"):
       return redirect("/")
    
    db = SQL("sqlite:///posts.db")
    posts=db.execute("SELECT * FROM posts WHERE completer IS NULL")

    return render_template("volunteerPosts.html", posts=posts)

@app.route("/redeempoints")
def redeempoints():
    return "Carriage"

@app.route("/viewhelper")
def viewhelper():
    return "Carriage"

@app.route("/changeinformation")
def changeinformation():
    return "Carriage"

@app.route("/verifyuser")
def verifyuser():
    return "Carriage"

@app.route("/logout")
def logout():
   session["username"] = None
   return redirect("/login")
