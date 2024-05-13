
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import sqlite3 as sql
import uuid
from flask import Flask, redirect, render_template, request, send_from_directory, session, url_for
from flask import Flask, request, render_template, jsonify
import torch
import torchvision.transforms as transforms
from PIL import Image
from EyeDiseasesDetector import EyeDiseaseDetector
from datetime import datetime

app = Flask(__name__)
app.secret_key="eyecare"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DR_IMAGES='dr_images'
app.config['DR_IMAGES'] = DR_IMAGES


@app.route('/Prediction', methods=['GET','POST'])
def Prediction():
    pred=""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'image_path' not in request.files:
            return jsonify({'error': 'No file uploaded'})

        file = request.files['image_path']

        # Check if the file is an image
        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        filename = str(uuid.uuid4()) + secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        model = EyeDiseaseDetector(num_classes=4)  # Assuming 5 classes
        model.load_state_dict(torch.load(os.path.join('model.pth')))
        model.eval()

        # Define transform for input data preprocessing
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])
        ])
        try:
            # Load and preprocess input image
            input_image = Image.open(file)
            input_tensor = transform(input_image)
            input_batch = input_tensor.unsqueeze(0)  # Add batch dimension

            # Make prediction
            with torch.no_grad():
                output = model(input_batch)
                _, predicted = torch.max(output.data, 1)

                print(f'Validation Accuracy: {100 * predicted }%')
                # Convert output to probabilities using softmax
                probabilities = torch.softmax(output, dim=1)

                # Extract predicted class label
                predicted_class = torch.argmax(probabilities, dim=1).item()

                # Print predicted class label
                print("Predicted class:", predicted_class)
        
                if(predicted_class==0):
                    pred='Cataracts'
                    #return render_template('Patient/result.html',prediction=pred) 
                elif(predicted_class==1):
                    pred='Diabetic Ratinopathy'
                    #return render_template('Patient/result.html',prediction=pred) 
                elif(predicted_class==2):
                    pred='Glaucoma'
                    ##return render_template('Patient/result.html',prediction=pred) 
                elif(predicted_class==3):
                    pred='Healthy Eyes'
                    #return render_template('Patient/result.html',prediction=pred) 
                else:
                    pred="Detect Undefined Deseases"
        except Exception as e:
            pred="Detect Undefined Deseases"
    return render_template('Patient/result.html',prediction=pred,filename=filename) 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    msg=request.args.get("msg")
    return render_template('login.html',msg=msg)

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/doctors', methods=['GET'])
def doctors():
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM doctors")
        doctors=cur.fetchall()
    return render_template('doctor.html',doctors=doctors)

@app.route('/departments', methods=['GET'])
def departments():
    return render_template('depatments.html')

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/Register', methods=['GET'])
def Register():
    return render_template('register.html')

@app.route('/RegisterDB', methods=['GET','POST'])
def RegisterDB():
    msg=''
    if request.method=='POST':
        try:
            Name=request.form['fullname']
            email=request.form['email']
            dob=request.form['dob']
            gender=request.form['gender']
            address=request.form['address']
            phone=request.form['phone']
            password=request.form['pass1']
            with sql.connect("eyecare.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO patients(name,address,phone,email,gender,dob) VALUES (?,?,?,?,?,?)",(Name,address,phone,email,gender,dob))
                cur.execute("SELECT * FROM patients ORDER BY id DESC")
                row=cur.fetchone()
                p_id=row[0]
                cur.execute("INSERT INTO users(username,password,typeid,type,name) VALUES (?,?,?,?,?)",(email,password,p_id,'P',Name))
                con.commit()
                msg = "Data Entered Sucessfully "
        except Exception as e:
            print(e)
            msg='Error in Insert Operation'
        finally:
            return redirect(url_for('login',msg=msg))

@app.route('/Authentication', methods=['GET','POST'])
def Authentication():
    msg=''
   
    #passing HTML form data into python variable
    uname=request.form['username']
    password=request.form['password']
    #creating variable for connection
    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(uname,password))
        print ("Opened database successfully")
        rows=cur.fetchone()
        if rows:
            session['loggedin']=True
            session['type_id']=rows[3]
            session['username']=rows[5]
            session['type']=rows[4]
            if session['type']=='P':
                return redirect(url_for('p_index'))
            elif session['type']=='A':
                return redirect(url_for('a_index'))
            elif session['type']=='D':
                return redirect(url_for('d_index'))
        else:
            return render_template('login.html',msg="User Name or Passwors are incorrect, Please Try Again")


@app.route('/p_index', methods=['GET','POST'])
def p_index():
    return render_template('Patient/p_index.html')

@app.route('/p_about', methods=['GET','POST'])
def p_about():
    return render_template('Patient/p_about.html')

@app.route('/p_doctor', methods=['GET','POST'])
def p_doctor():
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM doctors")
        doctors=cur.fetchall()
        cur.execute("SELECT doctors.name, count(msg.sender) as countofmsg from msg INNER JOIN doctors on msg.sender=doctors.name WHERE msg.status=? GROUP by doctors.name",(0,))
        chat_msg=cur.fetchall()
        print(chat_msg)
    return render_template('Patient/p_doctor.html',doctors=doctors,chat_msg=chat_msg)

@app.route('/p_department', methods=['GET','POST'])
def p_department():
    return render_template('Patient/p_departments.html')

@app.route('/p_appoinment', methods=['GET','POST'])
def p_appoinment():
    doctor=request.form['doct']
    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM slots")
        print ("Opened database successfully")
        slots=cur.fetchall()
        return render_template('Patient/p_appoinment.html',doct=doctor)

@app.route('/get_slots', methods=['GET','POST'])
def get_slots(date, doctor):
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM appoiment WHERE doctor=? AND date=?",(doctor,date,))
        appoinment_list=cur.fetchall()
        row_count = len(appoinment_list)
        print("Length: ",row_count)
       
       
        if row_count >0:
             print("Slot: ",appoinment_list[0][4])
             print("slotes: ", appoinment_list)
             cur.execute("SELECT * FROM slots WHERE slot!=?",(appoinment_list[0][4],))
             slots=cur.fetchall()
             print("slotes: ", slots)
        else:
            cur.execute("SELECT * FROM slots WHERE slot")
            slots=cur.fetchall()
            print("slotes: ", slots)
    return [(f"{slot[1]}", f"{slot}") for slot in slots]

@app.route('/date_changed', methods=['GET','POST'])
def date_changed():
    data = request.get_json()
    selected_date = data['date']
    doctor=data['doctor']
    slots = get_slots(selected_date, doctor)
    # Run your function here with the selected date
    print("Date changed to:", selected_date)
    print("Doctor:", doctor)
    # You can return a response if needed
    return jsonify(slots)

@app.route('/p_visiontest', methods=['GET','POST'])
def p_visiontest():
    return render_template('Patient/p_visiontest.html')

@app.route('/p_eyetest', methods=['GET','POST'])
def p_eyetest():
    return render_template('Patient/p_eyetest.html')

@app.route('/p_contact', methods=['GET'])
def p_contact():
    return render_template('Patient/p_contact.html')

@app.route('/p_appoinment_list', methods=['GET','POST'])
def p_appoinment_list():
    msg=request.args.get('msg')
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM appoiment WHERE user=?",(session['username'],))
        appointments=cur.fetchall()
        print(appointments)
    return render_template('Patient/p_appoinment_list.html',appointments=appointments,msg=msg)

@app.route('/AppoinmentDB', methods=['GET','POST'])
def AppoinmentDB():
    msg=''
    if request.method=='POST':
        try:
            doctor=request.form['doctor']
            date=request.form['dat']
            slot=request.form['slot']
            uname=session['username']
            cdat=datetime.now()
            with sql.connect("eyecare.db") as con:
                print ("Opened database successfully")
                cur = con.cursor()
                print ("Opened database successfully")
                #print(doctor,"/",date,"/",slot,"/",uid,"/",cdat)
                cur.execute("INSERT INTO appoiment(doctor,user,date,slot,bookdate,status) VALUES (?,?,?,?,?,?)",(doctor,uname,date,slot,cdat,'Pending'))
                print(cdat)
                print ("Opened database successfully")
                con.commit()
                print ("Opened database successfully")
                msg = "Data Entered Sucessfully "
        except Exception as e:
            print(e)
            msg='Error in Insert Operation'
        finally:
            return redirect(url_for('p_appoinment_list',msg=msg))
        
#Admin Section
@app.route('/a_index', methods=['GET','POST'])
def a_index():
    msg=request.args.get('msg')
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM doctors")
        doctors=cur.fetchall()
        cur.execute("SELECT * FROM appoiment")
        print ("Opened database successfully")
        appointments=cur.fetchall()
    return render_template('Admin/index.html',doctors=doctors,appointments=appointments,msg=msg)

@app.route('/adminProfile', methods=['GET','POST'])
def adminProfile():
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE typeid=?",(session['type_id'],))
        admin=cur.fetchall()
    return render_template('Admin/adminProfile.html',admin=admin)

@app.route('/add_doctor', methods=['GET','POST'])
def add_doctor():
    return render_template('Admin/hospital-add-doctor.html')

@app.route('/doctors_list', methods=['GET','POST'])
def doctors_list():
    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM doctors")
        print ("Opened database successfully")
        doctors=cur.fetchall()
    return render_template('Admin/doctor_list.html',doctors=doctors)

@app.route('/patient_list', methods=['GET','POST'])
def patient_list():
    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM patients")
        print ("Opened database successfully")
        patients=cur.fetchall()
    return render_template('Admin/patients_list.html',patients=patients)

@app.route('/appoinment_list', methods=['GET','POST'])
def appoinment_list():
    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM appoiment")
        print ("Opened database successfully")
        appointments=cur.fetchall()
    return render_template('Admin/appoinment_list.html',appointments=appointments)

@app.route('/doctor_profile/<int:doctor>', methods=['GET','POST'])
def doctor_profile(doctor):

    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM doctors where id=",doctor)
        print ("Opened database successfully")
        doctor=cur.fetchall()
    return render_template('Admin/doctor_profile.html',doctor=doctor)

@app.route('/add_doctorDB', methods=['GET','POST'])
def add_doctorDB():
     msg=""        
     if request.method=='POST':
        try:
            profilepic=request.files['profilepic']
            fullName=request.form['fullName']
            inputEmail=request.form['inputEmail']
            education=request.form['education']
            inputSpeciality=request.form['inputSpeciality']
            addreSs=request.form['addreSs']
            biO=request.form['biO']
            userName=request.form['userName']
            password=request.form['password']

            filename = str(uuid.uuid4()) + secure_filename(profilepic.filename)
            profilepic.save(os.path.join(app.config['DR_IMAGES'], filename))

            with sql.connect("eyecare.db") as con:
               
                cur = con.cursor()
                cur.execute("INSERT INTO doctors(name,mail,education,contact,bio,specialisations,pro_pic) VALUES (?,?,?,?,?,?,?)",(fullName,inputEmail,education,addreSs,biO,inputSpeciality,filename))
                cur.execute("SELECT * FROM doctors ORDER BY id DESC")
                row=cur.fetchone()
                d_id=row[0]
                cur.execute("INSERT INTO users(username,password,typeid,type,name) VALUES (?,?,?,?,?)",(userName,password,d_id,'D',fullName))
                con.commit()

                msg = "Data Entered Sucessfully "
        except Exception as e:
            print(e)
            msg='Data Entered Sucessfully '
        finally:
            return redirect(url_for('a_index', msg=msg))
        
@app.route('/delete_doctor', methods=['GET','POST'])
def delete_doctor():
    msg=""
    doctor_id=request.form['doct']
    with sql.connect("eyecare.db") as con:
            print ("Opened database successfully")
            cur = con.cursor()
            print ("Opened database successfully")
            cur.execute("DELETE FROM doctors WHERE id=?",(doctor_id))
            con.commit()
            msg="Doctor Deleted Sucessfully"     
    return redirect(url_for('a_index',msg=msg))

#Doctor Section
@app.route('/d_index', methods=['GET','POST'])
def d_index():
    msg=request.args.get('msg')
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM patients")
        patients=cur.fetchall()
        cur.execute("SELECT * FROM appoiment WHERE doctor=?",(session['username'],))
        appointments=cur.fetchall()
        cur.execute("SELECT patients.name, count(msg.sender) as countofmsg from msg INNER JOIN patients on msg.sender=patients.name WHERE msg.status=? GROUP by patients.name",(0,))
        chat_msg=cur.fetchall()
        print("Mesg Count: ",chat_msg)
        print ("Opened database successfully")
        '''try:
            cur.execute('SELECT patients.name, count(msg.sender) as countofmsg from msg INNER JOIN patients on msg.sender=patients.name WHERE msg.status=? GROUP by patients.name',(0,))
            msg_count=cur.fetchall()
            print("MSG COUNT: ", msg_count)
        except Exception as e:
            print("Error: ",e)'''
        
    return render_template('Doctor/index.html',patients=patients,appointments=appointments,chat_msg=chat_msg)

@app.route('/d_profile', methods=['GET','POST'])
def d_profile():
    with sql.connect("eyecare.db") as con:
        print ("Opened database successfully")
        cur = con.cursor()
        print ("Opened database successfully")
        cur.execute("SELECT * FROM doctors where id=?",(session['type_id'],))
        print ("Opened database successfully")
        doctor=cur.fetchall()
    return render_template('Doctor/doctor_profile.html',doctor=doctor)

@app.route('/update_appoiment', methods=['GET','POST'])
def update_appoiment():
    status=request.args.get('status')
    app_id=request.args.get('appoinment_id')
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("UPDATE appoiment SET status=? WHERE id=?",(status,app_id))
        msg="Status Update Sucessfully"
    return redirect(url_for('d_index',msg=msg))

@app.route('/d_chatbox', methods=['GET','POST'])
def d_chatbox():
    pat=request.form['pat']
    print(pat)
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("UPDATE msg SET status=? WHERE reciever=? AND sender=?",("1",session['username'],pat))
        cur.execute('SELECT * FROM msg WHERE (sender=? AND reciever=?) OR (sender=? AND reciever=?)',(pat,session['username'],session['username'],pat))
        messages=cur.fetchall()
        print(messages)
    return render_template("Doctor/d_chatbox.html",pat=pat,messages=messages)

   # return render_template("Doctor/d_chatbox.html",pat=pat)

@app.route('/chatbox', methods=['GET','POST'])
def chatbox():
    doct=request.form['doct']
    print(doct)
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("UPDATE msg SET status=? WHERE reciever=? AND sender=?",("1",session['username'], doct))
        cur.execute('SELECT * FROM msg WHERE (sender=? AND reciever=?) OR (sender=? AND reciever=?)',(session['username'],doct,doct,session['username']))
        messages=cur.fetchall()
        print(messages)
    return render_template("Patient/chatbox.html",doct=doct,messages=messages)

@app.route('/get_messages')
def get_messages():
    person = request.args.get('doct')
    #print(person)
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("UPDATE msg SET status=? WHERE reciever=? AND sender=?",("1",session['username'],person))
        cur.execute('SELECT * FROM msg WHERE (sender=? AND reciever=?) OR (sender=? AND reciever=?)',(session['username'],person,person,session['username']))
        messages=cur.fetchall()
        #con.close()
        return render_template("Patient/chatbox.html",doct=person,messages=messages)
    
@app.route('/d_get_messages')
def d_get_messages():
    person = request.args.get('pat')
    #print(person)
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute("UPDATE msg SET status=? WHERE reciever=? AND sender=?",("1",session['username'],person))
        cur.execute('SELECT * FROM msg WHERE (sender=? AND reciever=?) OR (sender=? AND reciever=?)',(session['username'],person,person,session['username']))
        messages=cur.fetchall()
        #con.close()
        return render_template("Doctor/d_chatbox.html",pat=person,messages=messages)

# API endpoint to add a new message
@app.route('/add_message', methods=['POST'])
def add_message():
    text = request.form['messageInput']
    doct = request.form['doctor']
    print("aaaa: ",doct)
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute('INSERT INTO msg (msg,reciever,sender,status, date_time) VALUES (?,?,?,?,?)', (text,doct,session['username'],"0",datetime.now().strftime("%d-%m-%y %I:%M %p")))
        con.commit()
        #con.close()
    return redirect(url_for('get_messages',doct=doct))

@app.route('/d_add_message', methods=['POST'])
def d_add_message():
    text = request.form['messageInput']
    pat = request.form['doctor']
    print("aaaa: ",pat)
    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute('INSERT INTO msg (msg,reciever,sender,status,date_time) VALUES (?,?,?,?,?)', (text,pat,session['username'],"0",datetime.now().strftime("%d-%m-%y %I:%M %p")))
        con.commit()
    return redirect(url_for('d_get_messages',pat=pat))

#Logout
@app.route('/logout', methods=['GET','POST'])
def logout():
    if id in session:
        session.pop(id,None)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

#uploadfile
@app.route('/uploadfile', methods=['GET','POST'])
def uploadfile():
    return render_template("fileupload.html")

@app.route('/uploaded', methods=['GET','POST'])
def uploaded():
    
    #ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    file = request.files['image_path']

    if file.filename == '':
        return redirect(request.url)
    
    filename = str(uuid.uuid4()) + secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    with sql.connect("eyecare.db") as con:
        cur = con.cursor()
        cur.execute('INSERT INTO image (file) VALUES (?)', (filename,))
        con.commit()

    return render_template("showimage.html",file=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/drimages/<filename>')
def drimages(filename):
    return send_from_directory(app.config['DR_IMAGES'], filename)


@app.route('/p_visiontest_new', methods=['GET','POST'])
def p_visiontest_new():
    return render_template('Patient/p_visiontest_new.html')

@app.route('/p_visiontest_newAA', methods=['GET','POST'])
def p_visiontest_newAA():
    return render_template('Patient/p_visiontest_newAA.html')

@app.route('/p_visiontest_newBB', methods=['GET','POST'])
def p_visiontest_newBB():
    return render_template('Patient/p_visiontest_newBB.html')

@app.route('/p_visiontest_newCC', methods=['GET','POST'])
def p_visiontest_newCC():
    return render_template('Patient/p_visiontest_newCC.html')

@app.route('/p_visiontest_newRight', methods=['GET','POST'])
def p_visiontest_newRight():
    score=request.form['volume']
    return render_template('Patient/p_visiontest_newRight.html',lscore=score)

@app.route('/p_visiontest_newRightAA', methods=['GET','POST'])
def p_visiontest_newRightAA():
    lscore=request.args.get('lscore')
    return render_template('Patient/p_visiontest_newRightAA.html',lscore=lscore)

@app.route('/p_visiontest_newQA', methods=['GET','POST'])
def p_visiontest_newQA():
    score=request.form['volume']
    lscore=request.form['lscore']
    return render_template('Patient/p_visiontest_newQA.html',rscore=score,lscore=lscore)

@app.route('/p_visiontest_Result', methods=['GET','POST'])
def p_visiontest_Result():
    rscore=int(request.form['rscore'])
    lscore=int(request.form['lscore'])
    qascore=int(request.form['qascore'])
    totalscore=int(((rscore+lscore+qascore)/300)*100)
    return render_template('Patient/p_visiontest_Result.html',rscore=rscore,lscore=lscore,qascore=qascore,totalscore=totalscore)

if __name__ == '__main__':
    app.run(debug=True)
