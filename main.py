import json
import os

import mysql
import mysql.connector
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, session

import siteSubmission
import testingtool
import queueHandler
from flask_session import Session

app = Flask(__name__)


@app.route('/blog/<parameter_name>')
def testTool(parameter_name):
    return render_template('blog.html', regdata=parameter_name.capitalize())


@app.route('/fetchData')
def fetchData():
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="shoLAY123@1",
        database="scrapiusdb"
    )
    db_cursor = db_connection.cursor(buffered=True)
    query = "select Site,data from scrapeddata where user=(%s)"
    db_cursor.execute(query, (session['loggedInEmail'],))
    myresult = db_cursor.fetchall()
    username = str(session['loggedInEmail'])
    file_name = 'userbase/' + username
    if not os.path.exists(file_name):
        os.makedirs(file_name)
    file_name = file_name + "/schema.json"
    if not os.path.exists(file_name):
        # Create the file if it doesn't exist
        with open(file_name, 'w') as file:
            file.write("{}")
    with open(file_name, 'r') as file:
        loadedData = json.load(file)
    cr_filename = 'userbase/' + username + "/created.json"
    if not os.path.exists(cr_filename):
        # Create the file if it doesn't exist
        with open(cr_filename, 'w') as file:
            file.write("{}")
    with open(cr_filename, 'r') as file:
        cr_loadedData = json.load(file)
    mTableData = []
    for key in loadedData.keys():
        mstr = ""
        for mkey in loadedData[key].keys():
            if mkey != "parent" :
                if mstr == "":
                    mstr = mkey.capitalize()
                else:
                    mstr = mstr + ", " + mkey.capitalize()
        innerData = {
            "site" : key,
            "schema" : mstr,
            "siteTotalScraped" : sum(1 for item in myresult if item[0] == key),
            "created" : cr_loadedData[key]
        }
        mTableData.append(innerData)

    mData = {
        "totalScraped": len(myresult),
        "lastScraped": "2m",
        "totalSites": len(loadedData.keys()),
        "totalView": "2.5K",
        "totalSubs": "50",
        "data": str(json.dumps(mTableData))
    }
    return f'{str(json.dumps(mData,indent=4))}'


# Edit Below
@app.route('/testing', methods=['GET','POST'])
def testing():
    # print("Accessed testing")
    if request.method == 'POST':
        data = request.json
        paramKey = request.json.keys()
        sData = {}
        for key in paramKey:
            if key == 'url':
                sData["url"] = data.get(key)
            elif data.get(key) != "":
                soup = BeautifulSoup(data.get(key), 'html.parser')
                outerTag = soup.find()
                sData[key] = {
                    "type": outerTag.name,
                    "atr": {
                        "id": outerTag.get('id'),
                        "class": outerTag.get('class')[0] if outerTag.get('class') is not None else ""
                    }
                }
                # if not attrValidator(request.form[key]):
                #     return f'{request.form[key]} do not contains id or class attribute.'
                # else:
        testScrap = testingtool.TestMyScraping(sData)
        # print("reaced out of loop 1")
        return str(json.dumps(testScrap.getReturnValue()))
    return ""


# {
#     url : {
#         "parent" : {
#             "type" : outerTag,
#             "atr" : {
#                 "id" : outerTag.get('id'),
#                 "class" : outerTag.get('class')
#             }
#         },
#         "heading" : {
#             ....
#         }
#     }
# }
#
# {
#     "url" : url,
#     "parent" : {
#         "type" : outerTag,
#         "atr" : {
#             "id" : outerTag.get('id'),
#             "class" : outerTag.get('class')
#         }
#     },
#     "heading" : {
#         ....
#     }
# }


# Edit above


@app.route('/fetchblog/<parameter_name>')
def fetchblog(parameter_name):
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="shoLAY123@1",
        database="scrapiusdb"
    )
    param = parameter_name
    db_cursor = db_connection.cursor(buffered=True)
    usernamequery = "select email from userbase where username=(%s) Limit 1"
    db_cursor.execute(usernamequery, (param,))
    umyresult = db_cursor.fetchall()
    if len(umyresult) == 0:
        return f'No User Found'
    else:
        print(umyresult[0])
        query = "select data from scrapeddata where user=(%s) ORDER BY createdTime DESC"
        db_cursor.execute(query, umyresult[0])
        myresult = db_cursor.fetchall()
        if len(myresult) == 0:
            return f'No Data Found';
        else:
            mblogdata = []
            for row in myresult:
                mblogdata.append(row[0])
            return f'{str(json.dumps(mblogdata))}'


@app.route('/userRegister', methods=['GET', 'POST'])
def userRegister():
    if request.method == 'POST':
        email = request.form['mail']
        password = request.form['password']
        username = request.form['username']
        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="shoLAY123@1",
            database="scrapiusdb"
        )
        db_cursor = db_connection.cursor(buffered=True)
        # if db_connection.is_connected():
        #     print('Connected to MySQL database')
        query = "Select * from userbase where email=(%s) OR username=(%s) Limit 1"
        db_cursor.execute(query, (email, username))
        myresult = db_cursor.fetchall()

        if len(myresult) == 0:
            query = "Insert into userbase (name, email, password, username) values (%s, %s, %s, %s)"
            db_cursor.execute(query, ('aa', email, password, username))
            db_connection.commit()
            session['loggedInEmail'] = email;
            session['loggedInUserName'] = username
            return redirect('/dashboard')
        else:
            param = {"isUniqueUser": "True"}
            for item in myresult:
                if item[1] == email:
                    param["isUniqueUser"] = 'False'
            return redirect(url_for('/', messages=json.dumps(param)))


@app.route('/userLogin', methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        email = request.form['mail']
        password = request.form['password']
        # print("Login => " + email + "    " + password)

        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="shoLAY123@1",
            database="scrapiusdb"
        )
        db_cursor = db_connection.cursor(buffered=True)
        query = "select email,password,username from userbase"
        db_cursor.execute(query)
        myresult = db_cursor.fetchall()
        isVerified = 0
        mUsername = "";
        for item in myresult:
            if item[0] == email:
                if item[1] == password:
                    isVerified = 2
                    mUsername = item[2]
                else:
                    isVerified = 1
        if isVerified == 2:
            session['loggedInEmail'] = email
            session['loggedInUserName'] = mUsername
            return redirect('/dashboard')
        elif isVerified == 1:
            # param = [str(isVerified),str(isVerified),str(isVerified)]
            return render_template('index.html', regData='Incorrect password')
        else:
            return render_template('index.html', regData='Email not found')


@app.route('/manageSite', methods=['GET', 'POST'])
def manageSite():
    # print(session['loggedInEmail'])
    # json_file = "sitedata.json"
    # existing_data = []
    # try:
    #     with open(json_file) as file:
    #         existing_data = json.load(file)
    # except FileNotFoundError:
    #     pass
    return render_template('newmanage.html')


def attrValidator(element1):
    soup = BeautifulSoup(element1, 'html.parser')
    outerTag = soup.find()
    if outerTag.has_attr('class'):
        if len(outerTag.get('class')) > 0:
            return True
    elif outerTag.has_attr('id'):
        if len(outerTag.get('id')) > 0:
            return True
    else:
        return False


@app.route('/addSite', methods=['GET', 'POST'])
def addSite():
    userEmail = session['loggedInEmail']
    mUrl = request.form['url']
    msg = ""
    paramKey = request.form.keys()
    # print(str(paramKey))
    if 'parent' in paramKey and not attrValidator(request.form['parent']):
        msg = "Parent do not contains id or class attribute."
    # elif 'heading' in paramKey and not attrValidator(request.form['heading']):
    #     msg = "Heading do not contains id or class attribute."
    # elif 'link' in paramKey and not attrValidator(request.form['link']):
    #     msg = "Link do not contains id or class attribute."
    # elif 'img' in paramKey and not attrValidator(request.form['img']):
    #     msg = "Image do not contains id or class attribute."
    if msg == "":
        sData = {}
        for key in paramKey :
            if request.form[key].strip() != "" and key != 'url':
                sData[key] = request.form[key];
        addSiteObj = siteSubmission.addSiteSubmission(userEmail, mUrl, sData)
        return redirect('/dashboard')
    else:
        print(msg)
        return render_template('manage.html', regData=msg)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    data = {
        "email": session['loggedInEmail'],
        "username": session['loggedInUserName']
    }
    return render_template('newdash.html', my_data=data)


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        json_file = "sitedata.json"
        new_data = {
            "url": request.form['siteBox'],
            "schema": request.form['schemaBox']
        }
        existing_data = []
        try:
            with open(json_file) as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            pass
        # Append the new dictionary to the existing data
        existing_data.append(new_data)
        # Write the updated data back to the JSON file
        with open(json_file, "w") as file:
            json.dump(existing_data, file)
    return redirect('/manageSite')


@app.route('/', methods=['GET', 'POST'])
def index():
    # existing_data = []
    # json_file = "sitedata.json"
    # try:
    #     with open(json_file) as file:
    #         existing_data = json.load(file)
    # except FileNotFoundError:
    #     pass
    # return render_template('index.html', regData=existing_data)
    if session.get('loggedInEmail') is not None:
        print(session['loggedInEmail'])
    return render_template('index.html')


if __name__ == "__main__":
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
    queueHandler.queuehandlerStarted()
    app.run()

