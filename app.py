from email import message
import textwrap
import pyodbc
from flask import Flask, render_template, Response, request
import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
from datetime import datetime
from flask_mail import Mail, Message

app=Flask(__name__)


data = [tuple()]
mail = Mail(app)
#configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'byfaceattendance@gmail.com'
app.config['MAIL_PASSWORD'] = 'Attendance@123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config[' MAIL_ASCII_ATTACHMENTS'] = True
mail = Mail(app)

#loading persons faces
path = 'images'
images = []
personNames = []
myList = os.listdir(path)
print(myList)
for cu_img in myList:
    current_Img = cv2.imread(f'{path}/{cu_img}')
    images.append(current_Img)
    personNames.append(os.path.splitext(cu_img)[0])
print(personNames)

#setting up sql
driver = 'ODBC Driver 18 for SQL Server'

#specify the server name and database name
server_name='attendancebyface'
database_name='attendance'

#creating a server string
server = '{server_name}.database.windows.net,1433' .format(server_name=server_name)

#defining username and password
username = "rahul"
password = "Attendance@123"

#create the full connection string.
connection_string = textwrap.dedent('''
    Driver={driver};
    Server={server};
    Database={database};
    Uid={username};
    Pwd={password};
    Encrypt=yes;
    TrustServerCertificate=no;
    Connection Timeout=30;
'''.format(
    driver=driver,
    server=server,
    database=database_name,
    username=username,
    password=password,
)
)

#create new PYODBC connection object
cnxn: pyodbc.Connection = pyodbc.connect(connection_string)

cnxn.autocommit = True

#create a new cursor object from connection
crsr : pyodbc.Cursor = cnxn.cursor()


def faceEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

def attendance(name):
    time_now = datetime.now()
    tStr = time_now.strftime('%H:%M:%S')
    dStr = time_now.strftime('%Y-%m-%d')
    #for checking if name already exists on that day
    check_sql = "SELECT * FROM Attendance where name = '{name}' and date = '{date}' ".format(name= name, date = dStr)
    crsr.execute(check_sql)
    present = crsr.fetchall()

    if len(present)==0:
        #defining insert query
        insert_sql="INSERT INTO Attendance (name,time,date) VALUES( ? , ? , ?)"

        #define record sets
        records=[(name,tStr,dStr),]
            
        #Execute insert statement
        crsr.executemany(insert_sql, records)

        #commiting
        crsr.commit()

encodeListKnown = faceEncodings(images)
print('All Encodings Complete!!!')

cap = cv2.VideoCapture(0)

def gen_frames():
 while True:
    ret, frame = cap.read()
    faces = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
    faces = cv2.cvtColor(faces, cv2.COLOR_BGR2RGB)

    facesCurrentFrame = face_recognition.face_locations(faces)
    encodesCurrentFrame = face_recognition.face_encodings(faces, facesCurrentFrame)

    for encodeFace, faceLoc in zip(encodesCurrentFrame, facesCurrentFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        # print(faceDis)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            name = personNames[matchIndex].upper()
            # print(name)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            attendance(name)

    ret, buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def convert(data):
    df = pd.DataFrame(data)
    file_name = 'attendance.xlsx'
    df.to_excel(file_name)

@app.route('/mark', methods=['GET', 'POST'])  #routing to attendance page
def mark():
    return render_template('mark.html')

#to see the attendance
@app.route('/view', methods=['GET', 'POST'])
def view():
    date = (request.form['date'])
    select_sql="Select name, time From Attendance WHERE date = '{date}'".format(date = date)
    crsr.execute(select_sql)
    global data
    data = crsr.fetchall()
    return render_template('view.html', value=data, dates= date)


#routing to see attendance
@app.route('/download', methods=['GET', 'POST'])  
def get():
    return render_template('attendance.html')

#sending mail
@app.route('/send_mail', methods = ['GET', 'POST'])
def send_mail():

    convert(data)
    email = request.form['email']
    
    msg = Message(
        'Hello',
        sender = 'byfaceattendance@gmail.com',
        recipients = ['15rahul.ra@gmail.com']
    )
    with app.open_resource("attendance.xlsx") as fp:
        msg.attach("attendance.xlsx","attendance/xlsx", fp.read())
    mail.send(msg)
    return render_template('sent.html')
    

#routing to main page
@app.route('/', methods =['Get', 'Post'])  
def index():
    return render_template('welcome.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__=='__main__':
    app.run(debug=True)