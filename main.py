import datetime
import os
import gridfs
import smtplib
import json
from flask_pymongo import PyMongo
from flask_apscheduler import APScheduler 
from bson import ObjectId
from flask import Flask, request,Response, render_template, session, redirect
import pymongo
import io
from flask import send_file
my_collections = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_collections['centralizedDatabase']
user_col = my_db['User']
staff_col = my_db['Instructor']
result_col = my_db['Test']
questions_col = my_db['questions']
elearning_col = my_db['elearning']
assignment_col = my_db['assignments']
subject_col=my_db['subjects']

app = Flask(__name__)
app.secret_key = "central_db"
app.config['MONGO_URI']='mongodb://localhost:27017/centralizedDatabase.assignments'
mongo=PyMongo(app)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/adminLogin")
def adminLogin():
    return render_template("adminLogin.html")


@app.route("/adminLogin1", methods=['post'])
def adminLogin1():
    username = request.form.get('username')
    password = request.form.get('password')
    print(username,password)
    if username == 'admin' and password == 'admin':
        session['role'] = 'Admin'
        return redirect("/adminHome")
    else:
        return render_template("adminLogin.html", message="Invalid Login Details")

@app.route("/adminHome")
def adminHome():
    return render_template("adminHome.html")

@app.route("/addsubjecthome")
def addsubjecthome():
    return render_template("addSubjects.html")

@app.route("/addsubject",methods=['post'])
def addsubject():
    subject=request.form.get('subject').capitalize()
    id=subject_col.find_one()
    if subject in id['subjects']:
        return render_template("addSubjects.html",message="Subject Already Present!!!",color="red")
    id=subject_col.update_one({"_id":ObjectId(id["_id"])},{"$push":{"subjects": subject }})
    # elearning_col.insert_one({"subject":subject,"content":""})
    id=assignment_col.find_one()
    return render_template("adminHome.html")

@app.route("/userRegister")
def userRegister():
    return render_template("/userRegister.html",get_subjectbystaff=get_subjectbystaff)

@app.route("/userRegister1", methods=['post'])
def userRegister1():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    sub1=request.form.get('subject1')
    sub2=request.form.get('subject2')
    sub1=eval(sub1)
    sub2=eval(sub2)
    sub1['instructor_id']=ObjectId(sub1['instructor_id'])
    sub2['instructor_id']=ObjectId(sub2['instructor_id'])
    print(sub1)
    print(sub2)
    print(type(sub1))
    if sub1['sub']==sub2['sub']:
        return render_template("userRegister.html", message="Duplicate Subject Not Allowed!!!.....", color="red",get_subjectbystaff=get_subjectbystaff)
    sub=[sub1,sub2]
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = user_col.count_documents(query)
    if count > 0:
        return render_template("userRegister.html", message="Duplicate Details!!!.....", color="red",get_subjectbystaff=get_subjectbystaff)
    query = {"name": name, "email": email, "phone": phone, "password": password, "subjects":sub}
    result = user_col.insert_one(query)
    user_id = result.inserted_id
    sub1['marks']=0
    # del sub1['instructor_id']
    # del sub2['instructor_id']
    sub2['marks']=0
    query = {"user_id": user_id, "subjects":sub}
    result_col.insert_one(query)
    # assignmentSubmission_col.insert_one(query)
    return render_template("userLogin.html", message="User Registered successfully", color="green")

@app.route("/userLogin")
def userLogin():
    print(datetime.datetime.now()+datetime.timedelta(minutes=15))
    return render_template("/userLogin.html")

@app.route("/userLogin1", methods=['post'])
def userLogin1():
    email = request.form.get('email')
    password = request.form.get('password')
    query = {"email": email, "password": password}
    count = user_col.count_documents(query)
    if count > 0:
        user = user_col.find_one(query)
        session['user_id'] = str(user['_id'])
        session['role'] = 'User'
        return redirect("/userHome")
    else:
        return render_template("userLogin.html", message="Invalid Login Details",color="red")

@app.route("/userHome")
def userHomeMain():
    return render_template("userHome.html")

@app.route("/staffRegister")
def staffRegister():
    return render_template("/staffRegister.html",get_subject=get_subject)

@app.route("/staffRegister1", methods=['post'])
def staffRegister1():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    sub1=request.form.get('subject1')
    sub2=request.form.get('subject2')
    if sub1==sub2:
        return render_template("staffRegister.html", message="Duplicate Subject Not Allowed!!!.....", color="red",get_subject=get_subject)
    sub=[sub1,sub2]
    print(sub1)
    print(sub2)
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = staff_col.count_documents(query)
    if count > 0:
        return render_template("staffRegister.html", message="Duplicate Details!!!.....", color="red",get_subject=get_subject)
    query = {"name": name, "email": email, "phone": phone, "password": password, "subjects":sub}
    staff_id = staff_col.insert_one(query).inserted_id
    questions_col.insert_one({"instructor_id":ObjectId(staff_id),"subject":sub1,"questions":[],"answers":[]})
    questions_col.insert_one({"instructor_id":ObjectId(staff_id),"subject":sub2,"questions":[],"answers":[]})
    assignment_col.insert_one({"instructor_id":ObjectId(staff_id),"subject":sub1,"file_id":"","due_date":"","student_marks":[]})
    assignment_col.insert_one({"instructor_id":ObjectId(staff_id),"subject":sub2,"file_id":"","due_date":"","student_marks":[]})
    return render_template("staffLogin.html", message="Instructor Registered successfully", color="green")

@app.route("/staffLogin")
def staffLogin():
    print(datetime.datetime.now()+datetime.timedelta(minutes=15))
    return render_template("/staffLogin.html")

@app.route("/staffLogin1", methods=['post'])
def staffLogin1():
    email = request.form.get('email')
    password = request.form.get('password')
    query = {"email": email, "password": password}
    count = staff_col.count_documents(query)
    if count > 0:
        user = staff_col.find_one(query)
        session['staff_id'] = str(user['_id'])
        session['role'] = 'Staff'
        return redirect("/staffHome")
    else:
        return render_template("staffLogin.html", message="Invalid Login Details",color="red")

@app.route("/staffHome")
def staffHome():
    print(session['role'])
    print(session['staff_id'])
    return render_template("staffHome.html")


@app.route("/elearningSelect")
def elearningSelect():
    user_id = session['user_id']
    query = {"user_id": ObjectId(user_id)}
    result = result_col.find_one(query)
    return render_template("elearningselect.html", get_user_id=get_user_id, result=result)

@app.route("/assignmentSelect")
def assignmentSelect():
    user_id = session['user_id']
    query = {"user_id": ObjectId(user_id)}
    result = result_col.find_one(query)
    return render_template("assignmentSelect.html", get_user_id=get_user_id, result=result,temp="submit")

@app.route("/assignmenthome")
def assignmenthome():
    data=assignment_col.find_one()
    subject=request.args.get('subject')
    d=eval(subject)
    subject=dict()
    subject['subject']=d['sub']
    subject['instructor_id']=d['instructor_id']
    subject_id=data['subject']
    file_id=assignment_col.find_one(subject)
    id=str(eval(str(file_id))['file_id'])
    if id!="":
        temp="upload"
    else:
        temp=""
    return render_template("userassignmentdownload.html",subject_id=subject_id,subject=subject,temp=temp)

@app.route("/download",methods=['get','post'])
def download():
    subject=request.args.get('subject')
    subject=eval(subject)
    # subject=dict()
    # subject['subject']=d['subject']
    # subject['instructor_id']=d['instructor_id']
    print(subject)
    file_id=eval(str(assignment_col.find_one(subject)))
    print(file_id)
    file=my_db.fs.files.find_one({'_id':ObjectId(file_id['file_id'])})
    print(file['filename'])
    downloc=os.path.join("C:\\Users\\nagac\\Downloads",file['filename'])
    fs=gridfs.GridFS(my_db,collection="fs")
    out_data=fs.get(file['_id']).read()
    with open(downloc,'wb') as output:
        output.write(out_data)
    return send_file(io.BytesIO(out_data),download_name=file['filename'],mimetype="application/pdf", as_attachment=True)

@app.route("/downloadbyfileid",methods=['get','post'])
def downloadbyfileid():
    file_id=request.args.get('file_id')
    file=my_db.fs.files.find_one({'_id':ObjectId(file_id)})
    print(file['filename'])
    downloc=os.path.join("C:\\Users\\nagac\\Downloads",file['filename'])
    fs=gridfs.GridFS(my_db,collection="fs")
    out_data=fs.get(file['_id']).read()
    with open(downloc,'wb') as output:
        output.write(out_data)
    return send_file(io.BytesIO(out_data),download_name=file['filename'],mimetype="application/pdf", as_attachment=True)
    

@app.route("/adminassignment")
def adminassignment():    
    return render_template("adminAssignment.html",get_all_subject=get_all_subject,temp="upload")

@app.route("/adminassignmentsubmitsub")
def adminassignmentsubmitsub():
    return render_template("adminAssignment.html",get_all_subject=get_all_subject,temp="submit")
    
@app.route("/adminassignmentsubmit")
def adminassignmentsubmit():
    session['subject']=request.args.get('subject')
    return render_template("adminassignmentsubmit.html",submitedfile=submitedfile,get_user_id=get_user_id)

def submitedfile():
    instruct_id=session['staff_id']
    print(instruct_id)
    submited_file=assignment_col.find_one({'subject':session['subject'],'instructor_id':ObjectId(instruct_id)})['student_marks']
    print(submited_file)
    return submited_file

@app.route("/adminassignmentdrop")
def adminassignmentdrop():
    subject=request.args.get('subject')
    instructor_id=session['staff_id']
    print("subject",subject)
    return render_template("adminAssignmentdrop.html",subject=subject,instructor_id=instructor_id)

@app.route("/adminfileupload",methods=['post'])
def adminfileupload():
    subject=request.form.get('subject')
    due_date=request.form.get('due_date')
    instructor_id=session['staff_id']
    files=request.files['assignqst']
    print("inn")
    print(type(files))
    file_id=mongo.save_file(files.filename,files)
    print(file_id)
    print(subject)
    print(instructor_id)
    print(due_date)
    assignment_col.update_one({"instructor_id":ObjectId(instructor_id),"subject":subject},{"$set":{"file_id": ObjectId(file_id),"due_date":due_date}})
    return render_template("adminAssignment.html",get_all_subject=get_all_subject)

@app.route("/userfileupload",methods=['post'])
def userfileupload():
    subject=request.form.get('subject')
    d=eval(subject)
    print(d)
    subject=dict()
    subject['subject']=d['subject']
    subject['instructor_id']=d['instructor_id']
    print(assignment_col.find_one(subject))
    files=request.files['assignqst']
    user_id = session['user_id']
    file_id=mongo.save_file(files.filename,files)
    query = {"user_id": ObjectId(user_id)}
    result = result_col.find_one(query)
    query1={"submittedfile_id":file_id,"marks":0,"user_id":ObjectId(user_id)}
    assignment_col.update_one(subject,{'$push': {'student_marks': query1}})
    return render_template("assignmentselect.html", get_user_id=get_user_id, result=result)


@app.route("/elearninghome")
def elearninghome():
    subject = request.args.get('subject')
    content=elearning_col.find_one({"subject":subject})['content']
    print(subject)
    if content=="":
        user_id = session['user_id']
        query = {"user_id": ObjectId(user_id)}
        result = result_col.find_one(query)
        return render_template("elearningselect.html", get_user_id=get_user_id, result=result,message="Content Not Available...",color="red")
    return render_template("elearningHome.html", subject=subject,get_elearning=get_elearning)

@app.route("/examSelect")
def examSelect():
    user_id = session['user_id']
    query = {"user_id": ObjectId(user_id)}
    result = result_col.find_one(query)
    return render_template("examSelect.html", get_user_id=get_user_id, result=result)

@app.route("/examHome")
def examHome():
    subject = request.args.get('subject')
    instructor_id=request.args.get('instructor_id')
    print(subject)
    if get_questions(subject)==[]:
        user_id = session['user_id']
        query = {"user_id": ObjectId(user_id)}
        result = result_col.find_one(query)
        return render_template("examSelect.html", get_user_id=get_user_id, result=result,message="Exam Not Available....",color="red")
    return render_template("examHome.html", examsubject=subject,instructor_id=instructor_id)

@app.route("/examPage")
def examPage():
    subject = request.args.get('exam_subject')
    instructor_id=request.args.get('instructor_id')
    print(subject)
    return render_template("test.html",get_questions=get_questions, examsubject=subject,instructor_id=instructor_id)

@app.route("/finish")
def examFinish():
    score=request.args.get('score')
    sub=request.args.get('subject')
    instructor_id=request.args.get('instructor_id')
    score_dic=json.loads(score)
    print(sub)
    print(instructor_id)
    query={'subject':sub,'instructor_id':ObjectId(instructor_id)}
    marks=0
    userid=session['user_id']
    print(userid)
    ans=questions_col.find_one(query)['answers']
    print(ans)
    print(ans)
    print(score_dic)
    for i in score_dic:
        if ans[i]==score_dic[i]:
            marks+=20
    print(marks)
    id=result_col.update_one({"user_id":ObjectId(userid),"subjects.sub":sub},{"$set":{"subjects.$.marks":marks}})
    print(id)
    return render_template("finish.html",marks=marks,eligiblecri=50)

@app.route("/results")
def result():
    # userid=session['user_id']
    if session['role']=='Staff':
        get_resultsbystaff()
        return render_template("results.html",get_user_id=get_user_id,get_resultsbystaff=get_resultsbystaff)
    elif session['role']=='User':
        return render_template("resultadmin.html",get_users=get_users,get_results=get_results)
    else:
        return render_template("resultadmin.html",get_users=get_users,get_results=get_results)

@app.route("/adminElearn")
def adminElearn():
    return render_template("adminElearn.html",get_all_subject=get_all_subject)

@app.route("/adminElearn1")
def adminElearn1():
    subject=request.args.get('subject')
    return render_template("subjectelearn.html",get_content=get_content,subject=subject)

@app.route("/subjectelearn",methods=['post'])
def subjectelearn():
    content=request.form.get('content')
    subject=request.form.get('subject')
    print(content)
    print(subject)
    elearning_col.update_one({'subject':subject},{"$set":{'content':content}})
    return render_template("adminElearn.html",message="Content Added Successfully",get_all_subject=get_all_subject,color="green")

@app.route("/adminQuestions")
def adminQuestions():
    return render_template("adminqst.html",get_all_subject=get_all_subject)

@app.route("/adminQuestions1")
def adminQuestions1():
    subject=request.args.get('subject')
    return render_template("subjectqst.html",get_qst=get_qst,subject=subject)

@app.route("/subjectqst",methods=['post'])
def subjectqst():
    qsts=request.form.get('qsts')
    answers=request.form.get('answers')
    print(type(qsts))
    qsts=qsts.replace("\'", "\"")
    answers=answers.replace("\'", "\"")
    json_list = []
    print(qsts)
    jsonload=json.loads(qsts)
    jsonans=json.loads(answers)
    print(type(jsonload))
    anslist=[]
    anslist.append(jsonans)
    json_list.append(jsonload)
    json.dumps(json_list)
    json.dumps(anslist)
    print(json_list)
    subject=request.form.get('subject')
    print(subject)
    questions_col.update_one({'instructor_id':ObjectId(session['staff_id']),"subject":subject},{"$set":{'questions':json_list[0],'answers':anslist[0]}})
    return render_template("adminqst.html",message="Questions Added Successfully",get_all_subject=get_all_subject,color="green")

def get_all_subject():
    print(session['role'])
    print(session['staff_id'])
    if session['role']=='Staff':
        subject=staff_col.find_one({"_id":ObjectId(session['staff_id'])})
        
    else:
        print("staff")
        subject=subject_col.find_one()
    # subjects = elearning_col.find()
    print(subject)
    return subject

def get_subject():
    subject=subject_col.find_one()
    return subject['subjects']

def get_subjectbystaff():
    subject=staff_col.find()
    return subject

def get_user_id(user_id):
    # print("in user id")
    # print(user_id)
    query = {'_id': user_id}
    user = user_col.find_one(query)
    return user

def get_users():
    users = user_col.find()
    return users


def get_questions(subject):
    print(subject)
    query = {'subject': subject}
    qsts = questions_col.find_one(query)
    return qsts['questions']

def get_elearning(subject):
    print(subject)
    query = {'subject': subject}
    elearn = elearning_col.find_one(query)
    return elearn

def get_content(subject):
    query={ 'subject': subject}
    content=elearning_col.find_one(query)
    return content

def get_qst(subject):
    query={'instructor_id':ObjectId(session['staff_id']),'subject': subject}
    qsts=questions_col.find_one(query)
    qsts['questions']=str(qsts['questions'])
    qsts['questions']=qsts['questions'].replace("\'", "\"")
    print(qsts)
    return qsts

def get_results(id):
    marks=result_col.find_one({'user_id':ObjectId(id)})
    return marks

def get_resultsbystaff():
    marks=result_col.find()
    res=[]
    for i in marks:
        res.append(i)
    for i in res:
        for j in i.get("subjects"):
            if ObjectId(j.get("instructor_id"))!=ObjectId(session["staff_id"]):
                i.get("subjects").remove(j)
    for i in res:
        for j in i.get("subjects"):
            if ObjectId(j.get("instructor_id"))!=ObjectId(session["staff_id"]):
                i.get("subjects").remove(j)
        if len(i.get("subjects"))==0:
            res.remove(i)
    print(res)
    return res

def get_assignemntbystaff():
    marks=result_col.find()
    res=[]
    for i in marks:
        res.append(i)
    for i in res:
        for j in i.get("subjects"):
            if ObjectId(j.get("instructor_id"))!=ObjectId(session["staff_id"]):
                i.get("subjects").remove(j)
    return res
if __name__=="__main__":
    app.run(debug=True,port=5001)
    
