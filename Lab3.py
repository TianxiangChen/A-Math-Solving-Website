from app import *
from app import db_config
from app import mail
import os
from flask import render_template, session, request, flash, redirect, url_for, send_from_directory, send_file, g
from app.forms.Forms import SignupForm, SigninForm, EasyUploadForm
from wand.image import Image
import random
import string
import boto3
from math_recog import math_recog
import datetime
import simplejson

from itsdangerous import URLSafeTimedSerializer
from app.email_config import mail_config

from functools import wraps


SUPPORTED_EXT = ['.jpg', '.jpeg', '.png']
RANDOM_LENGTH = 8
serializer = URLSafeTimedSerializer(mail_config['SECRET_KEY'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function


def check_confirmed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session['username']
        if db_config.user_check_confirmed(username) == False:
            return redirect(url_for('activate'))
        return f(*args, **kwargs)
    return decorated_function


@webapp.route('/')
@webapp.route('/index')
@webapp.route('/home')
def home():
    return render_template('home.html')

# handle error
@webapp.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


# @webapp.route('/test/FileUpload', methods=['GET', 'POST'])
# def test_file_upload():
#     if request.method == 'GET':
#         return render_template('testFileUpload.html')
#     else:
#         # POSTING
#         userID = request.form['userID']
#         passwd = request.form['password']
#         files = request.files.getlist('uploadedfile')
#         user = db_config.get_user(userID)
#         if not user:
#             return render_template('testFileUpload.html', error="User doesn't exist")
#         if not db_config.user_authenticate(user, password_pt=passwd):
#             return render_template('testFileUpload.html', error="Wrong password")
#
#         # user authenticated
#         save_photos(files, user)
#         return render_template('testFileUpload.html')

"""Signin page handler."""
@webapp.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if request.method == 'GET':
        if 'username' in session:
            # if user is logged in
            return redirect(url_for('activate'))
        return render_template('signin.html', form=form)
    elif request.method == 'POST':
        if not form.validate():
            return render_template('signin.html', form=form)
        else:
            # usr authenticated
            session['username'] = form.username.data

            user = db_config.get_user(session['username'])
            if not user:
                return 'user:db'

            session['username'] = form.username.data
            if db_config.user_check_confirmed(form.username.data) == False:
                return redirect(url_for('activate'))
            return redirect(url_for('profile'))


"""Process user signout, return to signin page."""
@webapp.route('/signout')
def signout():
    if 'username' not in session:
        return redirect(url_for('signin'))

    session.pop('username', None)
    return redirect(url_for('signin'))



"""Signup page, handles DB calls too."""
@webapp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if request.method == 'GET':
        if 'username' in session:
            # if user is logged in
            return redirect(url_for('profile'))

        return render_template('signup.html', form=form)

    elif request.method == 'POST':
        if form.validate():
            # validation succ
            db_config.add_user(form.username.data.lower(), form.password.data, form.email.data)

            # save cookie
            session['username'] = form.username.data

            return redirect(url_for('activate'))
        else:
            # validation failed
            return render_template('signup.html', form=form)


"""Activate user account to finish registration"""
@webapp.route('/activate')
@login_required
def activate():
    email = db_config.user_email(session['username'])
    encrypted_email = encrypt_email(email)
    return render_template('activate.html', email=email, encrypted_email=encrypted_email)


"""Activate user account to finish registration, a page for submitting send request"""
@webapp.route('/activate_send', methods = ['POST'])
@login_required
def activate_send():
    username = session['username']
    mail = db_config.user_email(username)
    token = generate_confirmation_token(mail)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('email.html', confirm_url=confirm_url)
    subject = "Please confirm your account registration"
    encrypted_email = encrypt_email(mail)
    result = send_email(mail, subject, html)
    if result == False:
        return render_template('retype_email.html', encrypted_email=encrypted_email)
    return render_template('activate_send.html', encrypted_email=encrypted_email)


@webapp.route('/retype_email', methods = ['GET', 'POST'])
@login_required
def retype_email():
    if request.method == 'POST':
        newEmail = request.form['new_email']
        db_config.set_user_email(session['username'], newEmail)
        return redirect(url_for('activate'))

@webapp.route('/confirm/<token>')
@login_required
def confirm_email(token):
    email = confirm_token(token)

    if email == False:
        msg = "The confirmation link is invalid or has expried."
        return render_template('confirm.html', msg=msg)

    username = db_config.get_user_by_email(email)[0]['username']
    result = db_config.user_check_confirmed(username)


    if db_config.user_check_confirmed(username) == True:
        msg = "Accout already confirmed. Please login."
    else:
        db_config.set_user_confirmed(username)
        msg = 'You have confimed your account.'
    return render_template('confirm.html', msg=msg)


"""Method called when uploading image, process images and stored to DB."""
@login_required
@check_confirmed
@webapp.route('/upload', methods=['POST'])
def upload():
    if not 'username' in session:
        return redirect(url_for('signin'))

    user = db_config.get_user(session['username'])
    if not user:
        return 'user:db'

    request_files = request.files.getlist("file")
    print(request_files)
    if request_files[0].filename == '':
        return render_template('upload.html', error='No file selected')

    save_photos(request_files, user)

    return redirect(url_for('profile'))


"""Helper used to send images to clients."""
@webapp.route('/upload/<path>/<filename>')
@login_required
@check_confirmed
def send_image(path, filename):
    return send_from_directory(os.path.join(IMAGE_STORE, path), filename)


"""Handles request for profile, packs all related images and send to user."""
@webapp.route('/profile')
@login_required
@check_confirmed
def profile():

    # locate the user
    user = db_config.get_user(session['username'])
    if not user:
        return 'user:db'

    #locate images by user
    images = db_config.get_user_question(session['username'])

    image_names = [photo.get('pic_url') for photo in images]
    image_and_transforms = {}
    for photo in images:
        image_and_transforms[S3_ADDR + photo.get('pic_url')] = [S3_ADDR + photo.get('pic_url'),
                                                                photo.get('input_latex'),
                                                                photo.get('soln_latex')]


    print(image_names)

    return render_template("profile.html", image_dict=image_and_transforms)


"""Displays form used to upload images"""
@webapp.route('/upload_form', methods=['get'])
@login_required
@check_confirmed
def upload_form():
    return render_template('upload.html', error=None)


@webapp.route('/about')
def about():
    return render_template('about.html')


@webapp.route('/qanda')
def qanda():
    status = user_logged_in()
    results = db_config.get_all_qanda()
    # results = simplejson.dumps(results)

    for result in results: # a stupid move, since angularJS compatibility of type decimal?
        result['qaid'] = int(str(result['qaid']))
    print(results)
    print(len(results))
    return render_template('qanda.html', results=results, status=status)


@webapp.route('/create_question')
@login_required
@check_confirmed
def create_question():
    return render_template('create_question.html')


@webapp.route('/submit_question', methods=['POST'])
def submit_question():
    question_title = request.form['question_title']
    question = request.form['question']
    author = session['username']

    db_config.create_qanda(question_title, question, author)
    return redirect(url_for('qanda'))


@webapp.route('/question_detail/<questionid>', methods=['GET'])
def question_detail(questionid):
    questionid = int(questionid)
    is_logged_in = user_logged_in()
    is_confirmed = int(db_config.user_check_confirmed(session['username']))
    # Get question details for questionid
    q_detail = db_config.get_a_qanda(questionid)
    answers = db_config.get_qanda_answers(questionid)

    questioner = q_detail['author']

    if user_logged_in():
        user_answered =  any(ans['ans_user'] ==  session['username'] for ans in answers)
        questioner_self = (questioner == session['username'])
    else:
        questioner_self = 0
        user_answered = 0

    is_solved = any(ans['ans_user'] ==  q_detail['best_ans_user'] for ans in answers)

    best_ans = 0
    if is_solved:
        best_ans = [ans for ans in answers if ans['ans_user'] == q_detail['best_ans_user']][0]
        answers.remove(best_ans)

    is_answered = 1
    if answers is None or len(answers) < 1:
        is_answered = 0

    return render_template('question_detail.html', q_detail=q_detail, answers=answers,
        is_answered=is_answered, user_answered=user_answered, questioner_self=questioner_self,
        is_solved=is_solved, best_ans=best_ans, is_logged_in=is_logged_in, is_confirmed = is_confirmed)


@webapp.route('/answer/<qaid>', methods=['POST'])
# answer a q&a question
def answer(qaid):
    if request.method == 'POST':
        answer = request.form['sol_form']
        answer_user = session['username']
        qaid = int(qaid)

        db_config.answer_a_question(qaid, answer, answer_user)
    return redirect(url_for('qanda'))

@webapp.route('/select_best_answer/<qaid>', methods=['POST'])
# select an answer as the best answer for a q&a question
def select_best_answer(qaid):
    if request.method == 'POST':
        qaid = int(qaid)
        ans_user = request.form['choice']
        # print(ans_user)
        db_config.choose_best_answer(qaid, ans_user)
    return redirect(url_for('qanda'))

def user_logged_in():
    return 'username' in session


"""Reads the list of uploaded files, process them and store to DB
under the given user"""
def save_photos(file_list, user):
   for upload_file in file_list:
        filename = upload_file.filename
        print('Filename: %s' % filename)

        # check file ext
        ext = os.path.splitext(filename)[1]
        if ext.lower() in SUPPORTED_EXT:
            print("File supported moving on...")
        else:
            return render_template('upload.html', error='Extension not supported')

        # make user folder
        user_image_folder = TMP_FOLDER
        if not os.path.exists(user_image_folder):
            os.makedirs(user_image_folder)

        # store image
        # randomize filename, used as a 'basefile'
        random_string = ''.join(random.choice(string.ascii_uppercase + string.digits)
                                for _ in range(RANDOM_LENGTH))
        filename = random_string + ext

        destination = os.path.join(user_image_folder, filename)
        print("Save upload to:", destination)
        upload_file.save(destination)
        original_filename = random_string + ext
        save_file(destination, filename)
        # transform images

        # do recognition
        question_latex, solution_latex = math_recog.process_img(destination)

        # scale down image
        with Image(filename=destination) as img:
            with img.clone() as resize:
                resize.transform(resize='640x480>')
                thumbnail_filename = random_string + '_thumb.jpg'
                destination = os.path.join(user_image_folder, thumbnail_filename)
                resize.save(filename=destination)
                save_file(destination, thumbnail_filename)

        clear_tmp_folder()

        # handle database
        db_config.create_question(session['username'],
                                  filename,
                                  question_latex,
                                  solution_latex)



def clear_tmp_folder():
    folder = TMP_FOLDER
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def save_file(file_to_save, filename):
    s3 = boto3.resource('s3')
    s3.Bucket(IMAGE_STORE).upload_file(file_to_save, filename)
    print("Saved %s to s3" % filename)


def encrypt_email(email):
    email_word_list = email.split('@')
    if len(email_word_list[0]) > 5:
        email_word_list[0] = email_word_list[0][0] + '***' +email_word_list[0][4:]
    elif len(email_word_list[0]) > 2:
        email_word_list[0] = email_word_list[0][0] + '*' +email_word_list[0][2:]
    else:
        email_word_list[0] = '*' * len(email_word_list[0])
    email_word_list = [email_word_list[0]] + ['@'] + [email_word_list[1]]
    encrypted_email = ''.join(email_word_list)
    return encrypted_email

def generate_confirmation_token(email):
    return serializer.dumps(email, salt = mail_config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    try:
        email = serializer.loads(
            token,
            salt = mail_config['SECURITY_PASSWORD_SALT'],
            max_age = expiration
        )
    except:
        return False
    return email

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender='tianxiang.chen@mail.utoronto.ca'
    )
    result = mail.send(msg)
    if result == None:
        return False
    return True

if __name__ == '__main__':
    webapp.run()
