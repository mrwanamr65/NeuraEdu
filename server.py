from flask import Flask, render_template, request, jsonify,url_for,redirect,session, Response,flash
from datetime import datetime
import mysql.connector
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, IntegerField,FileField
from wtforms.validators import DataRequired
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database_manager import (create_class,add_student,get_teachers2,
add_teacher,create_school_database,manager,add_video,delete_video,
delete_subject,add_subject_with_teacher_table, add_parent,
get_parent_data, add_parent_notification, fetch_all_parents_notifications,
delete_parent_notification,delete_evaluation,connection,get_student_data,
process_attendance_data,get_classes,teacher_data,headteacher_data,my_students,
fetch_all_notifications,add_student_evaluation,get_student_evaluations,
get_messages_for_user,send_message,get_teachers_with_shared_classes,
get_headteacher_data,is_valid_teacher_contact,get_teachers_for_headteacher,
is_valid_headteacher_contact,get_existing_conversations_for_parent,
get_teachers_for_parent,is_valid_parent_contact,get_all_classes,
get_classes_for_grade,get_attendance_data,calculate_statistics )
import os
from datetime import datetime
import json
from main import start_system,stop_system,is_running,initialize_multiprocessing
import multiprocessing
import logging
import re
import bleach



def server_1(primaryschool, middleschool, highschool):
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    limiter = Limiter(get_remote_address, app=app)
    if __name__ == "__main__":
        try:
            multiprocessing.freeze_support()
            initialize_multiprocessing()
            print("Multiprocessing system initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize multiprocessing system: {e}")
            raise RuntimeError("Failed to initialize multiprocessing system. Exiting.")
    logging.basicConfig(level=logging.DEBUG)







    def get_connection_by_stage(stage):
        if stage == "Elementary":
            return connection(primaryschool)
        elif stage == "Middle":
            return connection(middleschool)
        elif stage == "High":
            return connection(highschool)
        return None


    LIMIT = "100 per minute"



    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------------------------------------------------------------------------------#



    class StudentLoginForm(FlaskForm):
        class_ = SelectField('School Stage', choices=[('', '-- Select a stage --'), ('Elementary', 'Elementary school'), ('Middle', 'Middle school'), ('High', 'High school')], validators=[DataRequired()])
        student_grade = IntegerField('Grade', validators=[DataRequired()])
        student_class_num = IntegerField('Class Number', validators=[DataRequired()])
        student_code = IntegerField('Student Code', validators=[DataRequired()])
        student_password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Submit')



    class NotificationsForm(FlaskForm):
        student_code = StringField('Student Code', validators=[DataRequired()])
        class_name = StringField('Class Name', validators=[DataRequired()])
        submit = SubmitField('View Notifications')



    class EvaluationsForm(FlaskForm):
        student_code = StringField('Student Code', validators=[DataRequired()])
        class_name = StringField('Class Name', validators=[DataRequired()])
        school = StringField('School Stage', validators=[DataRequired()])
        submit = SubmitField('View Evaluations')


    class VideosForm(FlaskForm):
        class_name = StringField('Class Name', validators=[DataRequired()])
        school = StringField('School Stage', validators=[DataRequired()])
        submit = SubmitField('View Videos')

    

    class TeacherLoginForm(FlaskForm):
        school_stage = SelectField('School Stage', 
                                choices=[('Elementary', 'Elementary'), 
                                        ('Middle', 'Middle'), 
                                        ('High', 'High')],
                                validators=[DataRequired()])
        teacher_code = StringField('Teacher Code', validators=[DataRequired()])
        teacher_password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')



    class EducationAdminLoginForm(FlaskForm):
        school_stage = SelectField('School Stage', 
            choices=[
                ('Elementary', 'Elementary School'),
                ('Middle', 'Middle School'),
                ('High', 'High School')
            ], 
            validators=[DataRequired()]
        )
        admin_code = IntegerField('Admin Code', validators=[DataRequired()])
        admin_password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')




    @app.route('/', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)  
    def index():
        student_form = StudentLoginForm()
        teacher_form = TeacherLoginForm()
        admin_form = EducationAdminLoginForm()
        if request.method == 'POST':
            user_type = request.form.get('user_type')
            if user_type == 'student':
                return render_template('student.html', form=student_form)
            elif user_type == 'teacher':
                return render_template('teacher.html', form=teacher_form)
            elif user_type == 'headteacher':
                return render_template('headteacher.html')
            elif user_type == 'parent':
                return render_template('parent.html')
            elif user_type == 'education_admin':
                return render_template('education_admin.html', form=admin_form)
            else:
                return jsonify({"error": "Invalid user type"}), 400
        return render_template('main.html')

    
    



    @app.route('/student_login', methods=['POST'])
    @limiter.limit(LIMIT)  
    def student_login():
        form = StudentLoginForm()
        if form.validate_on_submit():
            class_ = form.class_.data
            student_grade = form.student_grade.data
            student_class_num = form.student_class_num.data
            student_code = form.student_code.data
            student_password = form.student_password.data

            if not re.match(r'^[A-Za-z]+$', class_):
                return render_template('student.html', form=form, error=bleach.clean('Invalid school stage format'))

            table_name = f"class{student_grade}_{student_class_num}"

            conn = get_connection_by_stage(class_)
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    f"SELECT * FROM `{table_name}` WHERE code = %s AND password = %s",
                    (student_code, student_password)
                )
                student = cursor.fetchone()
                if student:
                    session['user_type'] = 'student'
                    session['student_code'] = student_code
                    session['class_name'] = f"class{student_grade}_{student_class_num}"
                    session['school_stage'] = class_
                    return redirect('/student_dashboard')
                return render_template('student.html', form=form, error=bleach.clean('Invalid credentials'))
            except mysql.connector.errors.ProgrammingError as e:
                if "1146" in str(e):  
                    return render_template('student.html', form=form, error=bleach.clean(f"Class table {table_name} not found"))
                return render_template('student.html', form=form, error=bleach.clean('Database error occurred'))
            finally:
                conn.close()
        return render_template('student.html', form=form, error=bleach.clean('Invalid form submission'))









    @app.route('/notifications', methods=['POST'])
    def notifications():
        if 'user_type' not in session or session['user_type'] != 'student' or 'student_code' not in session or 'class_name' not in session:
            return redirect('/')

        form = NotificationsForm()
        if not form.validate_on_submit():
            return render_template('student_dashboard.html', error=bleach.clean('Invalid form submission'), 
                                notifications_form=form, evaluations_form=EvaluationsForm(), videos_form=VideosForm())

        student_code = form.student_code.data
        class_name = form.class_name.data
        school_stage = session['school_stage']

        if str(student_code) != str(session['student_code']) or class_name != session['class_name']:
            return render_template('student_dashboard.html', error=bleach.clean('Unauthorized access'), 
                                notifications_form=form, evaluations_form=EvaluationsForm(), videos_form=VideosForm())

        try:
            # _, grade, class_num = class_name.split('_')
            # grade = int(grade)
            # class_num = int(class_num)
            table_name = f"{class_name}_notifications"
        except ValueError:
            return render_template('student_dashboard.html', error=bleach.clean('Invalid class name format'), 
                                notifications_form=form, evaluations_form=EvaluationsForm(), videos_form=VideosForm())

        conn = get_connection_by_stage(school_stage)
        try:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                f"SELECT id, title, notification, notes FROM `{table_name}` ORDER BY id DESC"
            )
            notifications = cursor.fetchall()

            return render_template(
                'student_notifications.html',
                notifications=notifications,
                student_code=student_code,
                class_name=class_name,
                school=school_stage
            )
        except mysql.connector.errors.ProgrammingError as e:
            if "1146" in str(e):  
                return render_template('student_dashboard.html', error=bleach.clean(f"Notifications table {table_name} not found"), 
                                    notifications_form=form, evaluations_form=EvaluationsForm(), videos_form=VideosForm())
            return render_template('student_dashboard.html', error=bleach.clean('Database error occurred'), 
                                notifications_form=form, evaluations_form=EvaluationsForm(), videos_form=VideosForm())
        finally:
            conn.close()


    



    @app.route('/evaluations', methods=['POST'])
    def evaluations():
        if 'user_type' not in session or session['user_type'] != 'student' or 'student_code' not in session or 'class_name' not in session:
            return redirect('/')

        form = EvaluationsForm()
        if not form.validate_on_submit():
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Invalid form submission'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session['student_code']),
                                    class_name=session['class_name']
                                ), 
                                evaluations_form=form, 
                                videos_form=VideosForm(
                                    class_name=session['class_name'],
                                    school=session['school_stage']
                                ))

        student_code = form.student_code.data
        class_name = form.class_name.data
        school_stage = form.school.data

        if str(student_code) != str(session['student_code']) or class_name != session['class_name'] or school_stage != session['school_stage']:
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Unauthorized access'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session['student_code']),
                                    class_name=session['class_name']
                                ), 
                                evaluations_form=form, 
                                videos_form=VideosForm(
                                    class_name=session['class_name'],
                                    school=session['school_stage']
                                ))

 
        try:
            table_name = f"{class_name}_evaluations"
        except ValueError:
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Invalid class name format'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session['student_code']),
                                    class_name=session['class_name']
                                ), 
                                evaluations_form=form, 
                                videos_form=VideosForm(
                                    class_name=session['class_name'],
                                    school=session['school_stage']
                                ))

        conn = get_connection_by_stage(school_stage)
        try:
            cursor = conn.cursor(dictionary=True)
 
            cursor.execute(
                f"SELECT id, date, evaluation, note FROM `{table_name}` WHERE student_code = %s ORDER BY date DESC",
                (student_code,)
            )
            evaluations = cursor.fetchall()

       
            message = "No evaluations available." if not evaluations else None

            return render_template(
                'student_evaluations.html',   
                evaluations=evaluations,
                message=message,
                student_code=student_code,
                class_name=class_name,
                school=school_stage
            )
        except mysql.connector.errors.ProgrammingError as e:
            if "1146" in str(e):   
                return render_template('student_dashboard.html', 
                                    error=bleach.clean(f"Evaluations table {table_name} not found"), 
                                    notifications_form=NotificationsForm(
                                        student_code=str(session['student_code']),
                                        class_name=session['class_name']
                                    ), 
                                    evaluations_form=form, 
                                    videos_form=VideosForm(
                                        class_name=session['class_name'],
                                        school=session['school_stage']
                                    ))
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Database error occurred'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session['student_code']),
                                    class_name=session['class_name']
                                    ), 
                                evaluations_form=form, 
                                videos_form=VideosForm(
                                        class_name=session['class_name'],
                                        school=session['school_stage']
                                    ))
        finally:
            conn.close()







    @app.route('/student_educational_videos', methods=['POST'])
    def student_educational_videos():
        if 'user_type' not in session or session['user_type'] != 'student' or 'class_name' not in session or 'school_stage' not in session:
            return redirect('/')

        form = VideosForm()
        if not form.validate_on_submit():
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Invalid form submission'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', '')
                                ), 
                                evaluations_form=EvaluationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', ''),
                                    school=session.get('school_stage', '')
                                ), 
                                videos_form=form)

        class_name = form.class_name.data
        school_stage = form.school.data

        
        if class_name != session['class_name'] or school_stage != session['school_stage']:
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Unauthorized access'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', '')
                                ), 
                                evaluations_form=EvaluationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', ''),
                                    school=session.get('school_stage', '')
                                ), 
                                videos_form=form)

        try:
            # _, grade, class_num = class_name.split('_')
            # grade = int(grade)
            # class_num = int(class_num)
            table_name = f"{class_name}_videos"
            display_class_name = class_name
        except ValueError:
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Invalid class name format'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', '')
                                ), 
                                evaluations_form=EvaluationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', ''),
                                    school=session.get('school_stage', '')
                                ), 
                                videos_form=form)

        conn = get_connection_by_stage(school_stage)
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT id, link, subject, title FROM `{table_name}` ORDER BY id DESC"
            )
            videos = cursor.fetchall()

            message = "No educational videos available." if not videos else None

            return render_template(
                'student_educational_videos.html',
                videos=videos,
                message=message,
                class_name=display_class_name, 
                school=school_stage
            )
        except mysql.connector.errors.ProgrammingError as e:
            if "1146" in str(e):    
                return render_template('student_dashboard.html', 
                                    error=bleach.clean(f"Videos table {table_name} not found"), 
                                    notifications_form=NotificationsForm(
                                        student_code=str(session.get('student_code', '')),
                                        class_name=session.get('class_name', '')
                                    ), 
                                    evaluations_form=EvaluationsForm(
                                        student_code=str(session.get('student_code', '')),
                                        class_name=session.get('class_name', ''),
                                        school=session.get('school_stage', '')
                                    ), 
                                    videos_form=form)
            return render_template('student_dashboard.html', 
                                error=bleach.clean('Database error occurred'), 
                                notifications_form=NotificationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', '')
                                ), 
                                evaluations_form=EvaluationsForm(
                                    student_code=str(session.get('student_code', '')),
                                    class_name=session.get('class_name', ''),
                                    school=session.get('school_stage', '')
                                ), 
                                videos_form=form)
        finally:
            conn.close()






    @app.route('/student_dashboard', methods=['GET'])
    def student_dashboard():
        if 'user_type' not in session or session['user_type'] != 'student' or 'student_code' not in session or 'class_name' not in session:
            return redirect('/')

        student_code = session['student_code']
        class_name = session['class_name']
        school_stage = session['school_stage']

        try:
            table_name =class_name
        except ValueError:
            return render_template('student.html', error=bleach.clean('Invalid class name format'))

        conn = get_connection_by_stage(school_stage)
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT name FROM `{table_name}` WHERE code = %s",
                (student_code,)
            )
            student = cursor.fetchone()
            if not student:
                return render_template('student.html', error=bleach.clean('Student not found'))

            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            columns = cursor.fetchall()
            attendance_columns = [col['Field'] for col in columns if col['Field'].startswith('202')]

            schedule = []
            cursor.execute(
                f"SELECT {', '.join([f'`{col}`' for col in attendance_columns])} FROM `{table_name}` WHERE code = %s",
                (student_code,)
            )
            attendance = cursor.fetchone()
            if attendance:
                for col in attendance_columns:
                    status = attendance[col]
                    if status == 'True':   
                        display_status = 'Present'
                    elif status is None or status == '':
                        display_status = 'Absent'
                    else:
                        continue 
                    try:
                        date_str = f"{col[:4]}-{col[4:6]}-{col[6:8]}"
                        session_num = col[8:] or '1' 
                        schedule.append({
                            'date': date_str,
                            'session': session_num,
                            'status': display_status
                        })
                    except ValueError:
                        continue  

            notifications_form = NotificationsForm(
                student_code=str(student_code),
                class_name=class_name
            )
            evaluations_form = EvaluationsForm(
                student_code=str(student_code),
                class_name=class_name,
                school=school_stage
            )
            videos_form = VideosForm(
                class_name=class_name,
                school=school_stage
            )

            return render_template(
                'student_dashboard.html',
                name=student['name'],
                code=student_code,
                class_name=class_name,
                school=school_stage,
                schedule=schedule,
                notifications_form=notifications_form,
                evaluations_form=evaluations_form,
                videos_form=videos_form
            )
        except mysql.connector.errors.ProgrammingError as e:
            if "1146" in str(e):  
                return render_template('student.html', error=bleach.clean(f"Class table {table_name} not found"))
            return render_template('student.html', error=bleach.clean('Database error occurred'))
        finally:
            conn.close()






    @app.route('/teacher_login', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def teacher_login():
        form = TeacherLoginForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                school_stage = form.school_stage.data
                teacher_code = form.teacher_code.data
                teacher_password = form.teacher_password.data

                if school_stage not in ['Elementary', 'Middle', 'High']:
                    return render_template('teacher.html', form=form, error=bleach.clean('Invalid school stage'))

                conn = get_connection_by_stage(school_stage)
                if not conn:
                    return render_template('teacher.html', form=form, error=bleach.clean('Invalid school stage'))

                try:
                    result = teacher_data(conn, teacher_code, teacher_password, school_stage)
                    
                    if isinstance(result, Response):
                        return result
                    else:
                        return render_template('teacher.html', form=form, error=bleach.clean(result.get('error', 'Invalid credentials')))
                except mysql.connector.errors.ProgrammingError as e:
                    logging.error(f"Database error in teacher_login: {str(e)}")
                    return render_template('teacher.html', form=form, error=bleach.clean('Database error occurred'))
                except Exception as e:
                    logging.error(f"Unexpected error in teacher_login: {str(e)}")
                    return render_template('teacher.html', form=form, error=bleach.clean('An unexpected error occurred'))
                finally:
                    if conn.is_connected():
                        conn.close()
            else:
                return render_template('teacher.html', form=form, error=bleach.clean('Invalid form submission'))
        
        return render_template('teacher.html', form=form)





    @app.route('/teacher_dashboard', methods=['GET'])
    def teacher_dashboard():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        return render_template('teacher_dashboard.html', code=session['teacher_code'], school_stage=session['school_stage'])







    @app.route('/choose_class_attendance', methods=['GET', 'POST'])
    @limiter.limit(LIMIT) 
    def choose_class_attendance():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        code = session['teacher_code']
        stage = session['school_stage']
        
        connec = get_connection_by_stage(stage)
        if connec:
            try:
                return get_classes(connec, code, stage, 'student_attendance')
            except Exception as e:
                logging.error(f"Error in choose_class_attendance: {str(e)}")
                return jsonify({"error": "An error occurred while fetching classes"}), 500
            finally:
                if connec.is_connected():
                    connec.close()
        return jsonify({"error": "Invalid school stage"}), 400






    @app.route('/student_attendance', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)  
    def student_attendance():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']
        student_code = request.args.get('student_code')

        class_name_clean = bleach.clean(class_name) if class_name else None
        student_code_clean = bleach.clean(student_code) if student_code else None

        if not class_name_clean:
            return jsonify({"error": "Class name is required"}), 400

        conn = get_connection_by_stage(school)
        if not conn:
            return jsonify({"error": "Invalid school stage"}), 400

        try:
            students_data = my_students(class_name_clean, conn)
            if not students_data:
                return jsonify({"error": "No students found in this class"}), 404

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and student_code_clean:
                try:
                    student_code_int = int(student_code_clean)
                except ValueError:
                    return jsonify({"error": "Invalid student code format"}), 400

                student_data = get_student_data(conn, class_name_clean, student_code_int)
                if isinstance(student_data, tuple):
                    return jsonify({"error": student_data[0].get("error", "Error fetching student data")}), student_data[1]
                
                attendance_schedule = process_attendance_data(student_data)
                student_name = students_data.get(str(student_code_int), "Unknown")
                student_name_clean = bleach.clean(student_name)
                
                return jsonify({
                    "selected_student": student_name_clean,
                    "student_code": student_code_clean,
                    "attendance": [
                        {"date": entry["date"], "session": entry["session"], "status": entry["status"]}
                        for entry in attendance_schedule
                    ]
                })

            if student_code_clean:
                try:
                    student_code_int = int(student_code_clean)
                except ValueError:
                    return jsonify({"error": "Invalid student code format"}), 400

                student_data = get_student_data(conn, class_name_clean, student_code_int)
                if isinstance(student_data, tuple):
                    return jsonify({"error": student_data[0].get("error", "Error fetching student data")}), student_data[1]
                
                attendance_schedule = process_attendance_data(student_data)
                student_name = students_data.get(str(student_code_int), "Unknown")
                student_name_clean = bleach.clean(student_name)
                
                return render_template('student_attendance.html', 
                                    students=students_data, 
                                    class_name=class_name_clean, 
                                    school=school, 
                                    selected_student=student_name_clean, 
                                    student_code=student_code_clean, 
                                    attendance=attendance_schedule)
            else:
                return render_template('student_attendance.html', 
                                    students=students_data, 
                                    class_name=class_name_clean, 
                                    school=school)
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in student_attendance: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        except Exception as e:
            logging.error(f"Unexpected error in student_attendance: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
        finally:
            if conn.is_connected():
                conn.close()





    @app.route('/choose_class_evaluations', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def choose_class_evaluations():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        code = session['teacher_code']  
        stage = session['school_stage']  
        connec = get_connection_by_stage(stage)
        
        if connec:
            try:
                return get_classes(connec, code, stage, 'evaluate_class')
            except Exception as e:
                logging.error(f"Unexpected error in choose_class_evaluations: {str(e)}")
                return jsonify({"error": "Internal error occurred"}), 500
            finally:
                if connec.is_connected():
                    connec.close()
        return jsonify({"error": "Invalid school stage"}), 500






    @app.route('/evaluate_class', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def evaluate_class():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']
        teacher_code = session['teacher_code']

        class_name_clean = bleach.clean(class_name) if class_name else None
        school_clean = bleach.clean(school)
        teacher_code_clean = bleach.clean(teacher_code)

        if not class_name_clean:
            return jsonify({"error": "Class name is required"}), 400

        conn = get_connection_by_stage(school)  
        if not conn:
            return jsonify({"error": "Invalid school stage"}), 500

        try:
            students_data = my_students(class_name_clean, conn)
            if students_data:
                return render_template('evaluate_class.html', 
                                    students=students_data, 
                                    class_name=class_name_clean, 
                                    school=school_clean, 
                                    teacher_code=teacher_code_clean)
            return jsonify({"error": "No students found in this class"}), 404
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in evaluate_class: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        except Exception as e:
            logging.error(f"Unexpected error in evaluate_class: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
        finally:
            if conn and conn.is_connected():
                conn.close()







    @app.route('/add_evaluation', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def add_evaluation():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']
        student_code = request.args.get('student_code')
        teacher_code = session['teacher_code']

        # تنظيف الإدخال
        class_name_clean = bleach.clean(class_name) if class_name else None
        school_clean = bleach.clean(school)
        student_code_clean = bleach.clean(student_code) if student_code else None
        teacher_code_clean = bleach.clean(teacher_code)

        if not class_name_clean or not student_code_clean:
            return render_template('add_evaluation.html', 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                student_code=student_code_clean, 
                                student_name=None, 
                                teacher_code=teacher_code_clean, 
                                evaluations=[], 
                                current_date=datetime.now().strftime('%Y-%m-%d'), 
                                error="Class name and student code are required")

        conn = get_connection_by_stage(school_clean)
        if not conn:
            return render_template('add_evaluation.html', 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                student_code=student_code_clean, 
                                student_name=None, 
                                teacher_code=teacher_code_clean, 
                                evaluations=[], 
                                current_date=datetime.now().strftime('%Y-%m-%d'), 
                                error="Invalid school stage")

        try:
            students_data = my_students(class_name_clean, conn)
            if not students_data:
                return render_template('add_evaluation.html', 
                                    class_name=class_name_clean, 
                                    school=school_clean, 
                                    student_code=student_code_clean, 
                                    student_name=None, 
                                    teacher_code=teacher_code_clean, 
                                    evaluations=[], 
                                    current_date=datetime.now().strftime('%Y-%m-%d'), 
                                    error="No students found in this class")

            student_name = students_data.get(student_code_clean, "Unknown")
            student_name_clean = bleach.clean(student_name)
            evaluations = get_student_evaluations(conn, class_name_clean, student_code_clean)
            current_date = datetime.now().strftime('%Y-%m-%d')

            if not evaluations and not student_name_clean:
                return render_template('add_evaluation.html', 
                                    class_name=class_name_clean, 
                                    school=school_clean, 
                                    student_code=student_code_clean, 
                                    student_name=student_name_clean, 
                                    teacher_code=teacher_code_clean, 
                                    evaluations=[], 
                                    current_date=current_date, 
                                    error="Invalid class name or student code")

            if request.method == 'POST':
                evaluation = request.form.get('evaluation')
                note = request.form.get('note', '')
                evaluation_clean = bleach.clean(evaluation) if evaluation else None
                note_clean = bleach.clean(note) if note else ''

                if not evaluation_clean:
                    return render_template('add_evaluation.html', 
                                        class_name=class_name_clean, 
                                        school=school_clean, 
                                        student_code=student_code_clean, 
                                        student_name=student_name_clean, 
                                        teacher_code=teacher_code_clean, 
                                        evaluations=evaluations, 
                                        current_date=current_date, 
                                        error="Evaluation is required")

                success = add_student_evaluation(conn, class_name_clean, student_code_clean, evaluation_clean, note_clean)
                if success:
                    evaluations = get_student_evaluations(conn, class_name_clean, student_code_clean)
                    return render_template('add_evaluation.html', 
                                        class_name=class_name_clean, 
                                        school=school_clean, 
                                        student_code=student_code_clean, 
                                        student_name=student_name_clean, 
                                        teacher_code=teacher_code_clean, 
                                        evaluations=evaluations, 
                                        message="Evaluation added successfully!", 
                                        current_date=current_date)
                else:
                    return render_template('add_evaluation.html', 
                                        class_name=class_name_clean, 
                                        school=school_clean, 
                                        student_code=student_code_clean, 
                                        student_name=student_name_clean, 
                                        teacher_code=teacher_code_clean, 
                                        evaluations=evaluations, 
                                        current_date=current_date, 
                                        error="Failed to add evaluation")
            
            return render_template('add_evaluation.html', 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                student_code=student_code_clean, 
                                student_name=student_name_clean, 
                                teacher_code=teacher_code_clean, 
                                evaluations=evaluations, 
                                current_date=current_date)
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in add_evaluation: {str(e)}")
            return render_template('add_evaluation.html', 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                student_code=student_code_clean, 
                                student_name=None, 
                                teacher_code=teacher_code_clean, 
                                evaluations=[], 
                                current_date=datetime.now().strftime('%Y-%m-%d'), 
                                error="Database error occurred")
        except Exception as e:
            logging.error(f"Unexpected error in add_evaluation: {str(e)}")
            return render_template('add_evaluation.html', 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                student_code=student_code_clean, 
                                student_name=None, 
                                teacher_code=teacher_code_clean, 
                                evaluations=[], 
                                current_date=datetime.now().strftime('%Y-%m-%d'), 
                                error="An unexpected error occurred")
        finally:
            if conn and conn.is_connected():
                conn.close()








    @app.route('/delete_evaluation', methods=['POST'])
    @limiter.limit(LIMIT)
    def delete_evaluation_route():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return jsonify({'error': 'Unauthorized access'}), 401

        class_name = request.form.get('class_name')
        school = session['school_stage']  
        evaluation_id = request.form.get('evaluation_id')
        student_code = request.form.get('student_code')
        teacher_code = session['teacher_code']

        class_name_clean = bleach.clean(class_name) if class_name else None
        school_clean = bleach.clean(school)
        evaluation_id_clean = bleach.clean(evaluation_id) if evaluation_id else None
        student_code_clean = bleach.clean(student_code) if student_code else None
        teacher_code_clean = bleach.clean(teacher_code)

        if not all([class_name_clean, school_clean, evaluation_id_clean, student_code_clean]):
            logging.error(f"Missing required parameters: class_name={class_name_clean}, school={school_clean}, evaluation_id={evaluation_id_clean}, student_code={student_code_clean}")
            return jsonify({'error': 'Missing required parameters'}), 400

        if not evaluation_id_clean.isdigit():
            logging.error(f"Invalid evaluation_id format: {evaluation_id_clean}")
            return jsonify({'error': 'Invalid evaluation ID'}), 400

        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            logging.error(f"Invalid class_name format: {class_name_clean}")
            return jsonify({'error': 'Invalid class name format'}), 400

        conn = get_connection_by_stage(school_clean)  
        if conn is None:
            logging.error(f"Database connection failed for school: {school_clean}")
            return jsonify({'error': 'Database connection failed'}), 500
        try:
            success = delete_evaluation(conn, class_name_clean, evaluation_id_clean)
            if success:
                logging.info(f"Evaluation {evaluation_id_clean} deleted successfully for student {student_code_clean} in class {class_name_clean}")
                return jsonify({'message': 'Evaluation deleted successfully'}), 200
            else:
                logging.error(f"Evaluation {evaluation_id_clean} not found for student {student_code_clean} in class {class_name_clean}")
                return jsonify({'error': 'Evaluation not found'}), 404
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in delete_evaluation_route: {str(e)}")
            return jsonify({'error': 'Database error occurred'}), 500
        except Exception as e:
            logging.error(f"Unexpected error in delete_evaluation_route: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
        finally:
            if conn and conn.is_connected():
                conn.close()








    @app.route('/choose_class_my_students', methods=['POST', 'GET'])
    @limiter.limit(LIMIT)
    def choose_class_my_students():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        teacher_code = request.args.get('teacher_code')
        stage = session['school_stage']  
        teacher_code_clean = bleach.clean(teacher_code) if teacher_code else None
        stage_clean = bleach.clean(stage)

        if not teacher_code_clean:
            logging.error("Missing teacher_code in choose_class_my_students")
            return jsonify({"error": "Teacher code is required"}), 400

        connec = get_connection_by_stage(stage_clean)
        if connec is None:
            logging.error(f"Database connection failed for stage: {stage_clean}")
            return jsonify({"error": "Database connection failed"}), 500

        try:
            logging.info(f"Fetching classes for teacher {teacher_code_clean} in stage {stage_clean}")
            return get_classes(connec, teacher_code_clean, connec.database, 'class_details_my_students')
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in choose_class_my_students: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        except Exception as e:
            logging.error(f"Unexpected error in choose_class_my_students: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
        finally:
            if connec and connec.is_connected():
                connec.close()







    @app.route('/class_details_my_students', methods=['POST', 'GET'])
    @limiter.limit(LIMIT)
    def class_details_my_students():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']
        teacher_code = session['teacher_code']

        class_name_clean = bleach.clean(class_name) if class_name else None
        school_clean = bleach.clean(school)
        teacher_code_clean = bleach.clean(teacher_code)

        if not class_name_clean:
            logging.error("Missing class_name in class_details")
            return render_template('class_details_my_students.html', 
                                students={}, 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                teacher_code=teacher_code_clean, 
                                error="Class name is required")

        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            logging.error(f"Invalid class_name format: {class_name_clean}")
            return render_template('class_details_my_students.html', 
                                students={}, 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                teacher_code=teacher_code_clean, 
                                error="Invalid class name format")

        conn = get_connection_by_stage(school_clean)
        if conn is None:
            logging.error(f"Database connection failed for school: {school_clean}")
            return render_template('class_details_my_students.html', 
                                students={}, 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                teacher_code=teacher_code_clean, 
                                error="Database connection failed")

        try:
            students_data = my_students(class_name_clean, conn)
            if students_data:
                logging.info(f"Students data fetched successfully for class {class_name_clean} in school {school_clean}")
                return render_template('class_details_my_students.html', 
                                    students=students_data, 
                                    class_name=class_name_clean, 
                                    school=school_clean, 
                                    teacher_code=teacher_code_clean)
            else:
                logging.error(f"No students found for class {class_name_clean} in school {school_clean}")
                return render_template('class_details_my_students.html', 
                                    students={}, 
                                    class_name=class_name_clean, 
                                    school=school_clean, 
                                    teacher_code=teacher_code_clean, 
                                    error="No students found in this class")
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in class_details: {str(e)}")
            return render_template('class_details_my_students.html', 
                                students={}, 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                teacher_code=teacher_code_clean, 
                                error="Database error occurred")
        except Exception as e:
            logging.error(f"Unexpected error in class_details: {str(e)}")
            return render_template('class_details_my_students.html', 
                                students={}, 
                                class_name=class_name_clean, 
                                school=school_clean, 
                                teacher_code=teacher_code_clean, 
                                error="An unexpected error occurred")
        finally:
            if conn and conn.is_connected():
                conn.close()









    @app.route('/choose_class_notifications', methods=['GET', 'POST'])
    def choose_class_notifications():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        code = session['teacher_code']
        stage = session['school_stage']

        connec = get_connection_by_stage(stage)
        if connec:
            try:
                return get_classes(connec, code, connec.database, 'notification')
            except Exception as e:
                logging.error(f"Unexpected error in choose_class_notifications: {str(e)}")
                return jsonify({"error": "Internal error occurred"}), 500
            finally:
                if connec.is_connected():
                    connec.close()
        return jsonify({"error": "Invalid school stage"}), 500


    @app.route('/notifications_teacher', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def notification():
        if session.get('user_type') != 'teacher' or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']

        class_name_clean = bleach.clean(class_name) if class_name else None
        school_clean = bleach.clean(school)

        if not class_name_clean:
            return jsonify({"error": "Class name is required"}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            return jsonify({"error": "Invalid class name format"}), 400

        cncter = get_connection_by_stage(school_clean)
        if not cncter:
            return jsonify({"error": "Invalid school stage"}), 500

        try:
            notifications_ = fetch_all_notifications(cncter, class_name_clean)
            return render_template(
                'notifications.html',
                notifications=notifications_ or [],
                class_name=class_name_clean,
                school=school_clean,
                error=None if notifications_ else "No notifications found"
            )
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in notification: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        except Exception as e:
            logging.error(f"Unexpected error in notification: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
        finally:
            if cncter.is_connected():
                cncter.close()


    @app.route('/add_notification', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def add_notification():
        if session.get('user_type') != 'teacher' or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']

        class_name_clean = bleach.clean(class_name) if class_name else None
        school_clean = bleach.clean(school)

        if request.method == 'POST':
            title = request.form.get('title')
            notification = request.form.get('notification')
            notes = request.form.get('notes')

            title_clean = bleach.clean(title) if title else None
            notification_clean = bleach.clean(notification) if notification else None
            notes_clean = bleach.clean(notes) if notes else None

            if not class_name_clean or not title_clean or not notification_clean:
                return jsonify({"error": "Missing required fields"}), 400
            if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
                return jsonify({"error": "Invalid class name format"}), 400

            cncter = get_connection_by_stage(school_clean)
            if not cncter:
                return jsonify({"error": "Invalid school stage"}), 500

            try:
                cursor = cncter.cursor()
                insert_query = f"INSERT INTO {class_name_clean}_notifications (title, notification, notes) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (title_clean, notification_clean, notes_clean))
                cncter.commit()
                cursor.close()
                return jsonify({"message": "Notification added successfully"}), 200
            except mysql.connector.errors.ProgrammingError as e:
                logging.error(f"Database error in add_notification: {str(e)}")
                return jsonify({"error": "Database error occurred"}), 500
            except Exception as e:
                logging.error(f"Unexpected error in add_notification: {str(e)}")
                return jsonify({"error": "An unexpected error occurred"}), 500
            finally:
                if cncter.is_connected():
                    cncter.close()

        if not class_name_clean:
            return jsonify({"error": "Class name is required"}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            return jsonify({"error": "Invalid class name format"}), 400

        return render_template('add_notification.html', class_name=class_name_clean, school=school_clean)


    @app.route('/delete_notification', methods=['POST'])
    @limiter.limit(LIMIT)
    def delete_notification():
        if session.get('user_type') != 'teacher' or not session.get('school_stage'):
            return jsonify({"error": "Unauthorized access"}), 401

        class_name = request.form.get('class_name')
        notification_id = request.form.get('notification_id') or request.form.get('id')
        school = session['school_stage']

        class_name_clean = bleach.clean(class_name) if class_name else None
        id_clean = bleach.clean(notification_id) if notification_id else None
        school_clean = bleach.clean(school)

        if not class_name_clean or not id_clean:
            return jsonify({"error": "Missing required parameters"}), 400
        if not id_clean.isdigit():
            return jsonify({"error": "Invalid notification ID"}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            return jsonify({"error": "Invalid class name format"}), 400

        cncter = get_connection_by_stage(school_clean)
        if not cncter:
            return jsonify({"error": "Invalid school stage"}), 500

        try:
            cursor = cncter.cursor()
            delete_query = f"DELETE FROM {class_name_clean}_notifications WHERE id = %s"
            cursor.execute(delete_query, (id_clean,))
            cncter.commit()
            cursor.close()
            return jsonify({"message": "Notification deleted successfully"}), 200
        except mysql.connector.errors.ProgrammingError as e:
            logging.error(f"Database error in delete_notification: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        except Exception as e:
            logging.error(f"Unexpected error in delete_notification: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
        finally:
            if cncter.is_connected():
                cncter.close()










    @app.route('/teacher_videos', methods=['GET'])
    @limiter.limit(LIMIT)
    def teacher_videos():
        if session.get('user_type') != 'teacher' or not session.get('teacher_code') or not session.get('school_stage'):
            return redirect(url_for('index'))

        code = session['teacher_code']
        stage = session['school_stage']

        conn = get_connection_by_stage(stage)
        if conn:
            try:
                return get_classes(conn, code, conn.database, 'teacher_class_videos')
            except Exception as e:
                logging.error(f"Error in teacher_videos: {str(e)}")
                return jsonify({"error": "Internal error"}), 500
            finally:
                conn.close()
        return jsonify({"error": "Invalid school stage"}), 500






    @app.route('/teacher_class_videos', methods=['GET'])
    @limiter.limit(LIMIT)
    def teacher_class_videos():
        if session.get('user_type') != 'teacher' or not session.get('school_stage'):
            return redirect(url_for('index'))

        class_name = request.args.get('class_name')
        school = session['school_stage']
        teacher_code = session['teacher_code']

        if not class_name or not re.match(r'^[a-zA-Z0-9_]+$', class_name):
            return jsonify({"error": "Invalid class name"}), 400

        conn = get_connection_by_stage(school)

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name FROM subjects")
            all_subjects = [row['name'].strip().lower() for row in cursor.fetchall()]

            editable_subjects = []
            for subject in all_subjects:
                if not re.match(r'^[a-zA-Z0-9_]+$', subject):
                    continue
                cursor.execute(f"SELECT teacher_code FROM `{subject}`")
                teacher_codes = [str(row['teacher_code']) for row in cursor.fetchall()]
                if str(teacher_code) in teacher_codes:
                    editable_subjects.append(subject)

            cursor.execute(f"SELECT id, link, subject, title FROM {class_name}_videos")
            videos = cursor.fetchall()

            videos_by_subject = {subject: [] for subject in all_subjects}
            for video in videos:
                subject_key = video['subject'].strip().lower()
                videos_by_subject.setdefault(subject_key, []).append(video)

            return render_template(
                'teacher_class_videos.html',
                videos_by_subject=videos_by_subject,
                class_name=class_name,
                school=school,
                teacher_code=teacher_code,
                editable_subjects=editable_subjects
            )
        except Exception as e:
            logging.error(f"Error in teacher_class_videos: {str(e)}")
            return jsonify({"error": "Internal error"}), 500
        finally:
            conn.close()






    @app.route('/add_video', methods=['POST'])
    @limiter.limit(LIMIT)
    def add_video_route():
        if session.get('user_type') != 'teacher' or not session.get('school_stage'):
            return jsonify({"error": "Unauthorized"}), 403

        class_name = request.form.get('class_name')
        school = session['school_stage']
        subject = request.form.get('subject')
        title = request.form.get('title')
        link = request.form.get('link')

        if not all([class_name, subject, title, link]):
            return jsonify({'error': 'Missing required fields'}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
            return jsonify({'error': 'Invalid class name'}), 400

        conn = get_connection_by_stage(school)

        try:
            success = add_video(conn, class_name, link.strip(), subject.strip(), title.strip())
            if success:
                logging.info(f"Teacher {session['teacher_code']} added video to {class_name}")
                return jsonify({'message': 'Video added successfully'}), 200
            else:
                return jsonify({'error': 'Failed to add video'}), 500
        except Exception as e:
            logging.error(f"Error in add_video: {str(e)}")
            return jsonify({'error': 'Internal error'}), 500
        finally:
            conn.close()






    @app.route('/delete_video', methods=['POST'])
    @limiter.limit(LIMIT)
    def delete_video_route():
        if session.get('user_type') != 'teacher' or not session.get('school_stage'):
            return jsonify({"error": "Unauthorized"}), 403

        class_name = request.form.get('class_name')
        video_id = request.form.get('video_id')
        school = session['school_stage']

        if not class_name or not video_id:
            return jsonify({'error': 'Missing required fields'}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name) or not video_id.isdigit():
            return jsonify({'error': 'Invalid parameters'}), 400

        conn = conn = get_connection_by_stage(school)

        try:
            success = delete_video(conn, class_name, video_id)
            if success:
                logging.info(f"Teacher {session['teacher_code']} deleted video {video_id} from {class_name}")
                return jsonify({'message': 'Video deleted successfully'}), 200
            else:
                return jsonify({'error': 'Failed to delete video'}), 500
        except Exception as e:
            logging.error(f"Error in delete_video: {str(e)}")
            return jsonify({'error': 'Internal error'}), 500
        finally:
            conn.close()















    @app.route('/headteacher_login', methods=['POST', 'GET'])
    @limiter.limit(LIMIT)
    def headteacher_login():
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405

        school_stage = request.form.get('school_stage')
        code = request.form.get('headteacher_code')
        password = request.form.get('headteacher_password')

        if not school_stage or not code or not password:
            return jsonify({"error": "Missing required fields"}), 400
        if not code.isdigit():
            return jsonify({"error": "Invalid headteacher code format"}), 400

        conn = get_connection_by_stage(school_stage)
        if not conn:
            return jsonify({"error": "Invalid school stage"}), 400

        try:
            result = headteacher_data(conn, int(code), password, school_stage)
            return result
        finally:
            if conn and conn.is_connected():
                conn.close()


    @app.route('/headteacher_dashboard', methods=['GET'])
    def headteacher_dashboard_page():
        if session.get('user_type') != 'headteacher' \
        or not session.get('headteacher_code') \
        or not session.get('school_stage'):
            return redirect(url_for('index'))

        code = session['headteacher_code']
        school_stage = session['school_stage']

        return render_template('headteacher_dashboard.html',
                            code=bleach.clean(code),
                            school_stage=bleach.clean(school_stage))








 


    @app.route('/manage_classes', methods=['GET', 'POST'])
    def head_classes():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            try:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES LIKE 'class%'")
                raw_tables = cursor.fetchall()
                all_tables = [row[0] for row in raw_tables]
                classes = [table for table in all_tables if not table.endswith(('_evaluations', '_notifications', '_videos'))]

                if request.method == 'POST':
                    new_class = request.form.get('class_name')

                    if new_class and re.match(r'^[a-zA-Z0-9_]+$', new_class) and new_class.startswith('class') and not new_class.endswith(('_evaluations', '_notifications', '_videos')):
                        success = create_class(conn, new_class)
                        if success:
                            return jsonify({'message': f'Class {new_class} added successfully'}), 200
                        return jsonify({'error': 'Failed to add class'}), 500

                    return jsonify({'error': 'Invalid class name'}), 400

                return render_template('manage_classes.html', classes=classes, stage=stage)
            finally:
                if conn and conn.is_connected():
                    conn.close()
        except mysql.connector.Error as err:
            logging.error(f"Database Error in manage_classes: {err}")
            return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            logging.error(f"Unexpected error in manage_classes: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500


    @app.route('/configure_classes', methods=['GET'])
    def configure_classes():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            try:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES LIKE 'class%'")
                raw_tables = cursor.fetchall()
                all_tables = [row[0] for row in raw_tables]
                classes = [table for table in all_tables if not table.endswith(('_evaluations', '_notifications', '_videos'))]

                config_path = "config/classes_config.json"
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        class_configs = json.load(f)
                else:
                    class_configs = []

                configured_classes = []
                for cls in classes:
                    cls_cleaned = cls.strip().lower()
                    config = next((c for c in class_configs if c['class_name'].strip().lower() == cls_cleaned), None)
                    if config:
                        configured_classes.append({
                            'class_name': cls,
                            'configured': True,
                            'faces_path': config['faces_path'],
                            'dbname': config['dbname'],
                            'cam_num': config['cam_num'],
                            'config_file': config['config_file']
                        })
                    else:
                        configured_classes.append({
                            'class_name': cls,
                            'configured': False
                        })

                schedule_path = "config/schedules.json"
                if os.path.exists(schedule_path):
                    with open(schedule_path, 'r') as f:
                        schedules = json.load(f)
                else:
                    schedules = {"classes_times": []}

                return render_template('configure_classes.html',
                                    classes=configured_classes,
                                    schedules=schedules,
                                    stage=stage)
            finally:
                if conn and conn.is_connected():
                    conn.close()
        except mysql.connector.Error as err:
            logging.error(f"Database Error in configure_classes: {err}")
            return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            logging.error(f"Unexpected error in configure_classes: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500


    @app.route('/configure_class', methods=['POST'])
    def configure_class():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            data = request.get_json()
            class_name = data.get('class_name')
            cam_num = data.get('cam_num')

            if not class_name or cam_num is None:
                return jsonify({'error': 'Missing class name or camera number'}), 400

            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                return jsonify({'error': 'Invalid class name'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            try:
                dbname = conn.database

                config_path = "config/classes_config.json"
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        class_configs = json.load(f)
                else:
                    class_configs = []

                new_config = {
                    "faces_path": f"./faces/{class_name}",
                    "dbname": dbname,
                    "class_name": class_name,
                    "cam_num": int(cam_num),
                    "config_file": "./config/schedules.json"
                }
                class_configs.append(new_config)

                with open(config_path, 'w') as f:
                    json.dump(class_configs, f, indent=4)

                return jsonify({'message': f'Class {class_name} configured successfully'}), 200
            finally:
                if conn and conn.is_connected():
                    conn.close()
        except Exception as e:
            logging.error(f"Error in configure_class: {str(e)}")
            return jsonify({'error': str(e)}), 500


    @app.route('/update_class_config', methods=['POST'])
    def update_class_config():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            data = request.get_json()
            class_name = data.get('class_name')
            cam_num = data.get('cam_num')

            if not class_name or cam_num is None:
                return jsonify({'error': 'Missing class name or camera number'}), 400

            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                return jsonify({'error': 'Invalid class name'}), 400

            config_path = "config/classes_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    class_configs = json.load(f)
            else:
                return jsonify({'error': 'Configuration file not found'}), 404

            updated = False
            for config in class_configs:
                if config['class_name'] == class_name:
                    config['cam_num'] = int(cam_num)
                    updated = True
                    break

            if not updated:
                return jsonify({'error': 'Class not found in configuration'}), 404

            with open(config_path, 'w') as f:
                json.dump(class_configs, f, indent=4)

            return jsonify({'message': f'Class {class_name} configuration updated successfully'}), 200
        except Exception as e:
            logging.error(f"Error in update_class_config: {str(e)}")
            return jsonify({'error': str(e)}), 500


    @app.route('/update_schedule', methods=['POST'])
    def update_schedule():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            data = request.get_json()
            index = data.get('index')
            start_time = data.get('start_time')
            end_time = data.get('end_time')

            if index is None or not start_time or not end_time:
                return jsonify({'error': 'Missing index, start time, or end time'}), 400

            schedule_path = "config/schedules.json"
            if os.path.exists(schedule_path):
                with open(schedule_path, 'r') as f:
                    schedules = json.load(f)
            else:
                schedules = {"classes_times": []}

            if not isinstance(index, int) or index < 0 or index >= len(schedules.get('classes_times', [])):
                return jsonify({'error': 'Invalid schedule index'}), 400

            schedules['classes_times'][index] = [start_time, end_time]

            with open(schedule_path, 'w') as f:
                json.dump(schedules, f, indent=4)

            return jsonify({'message': 'Schedule updated successfully'}), 200
        except Exception as e:
            logging.error(f"Error in update_schedule: {str(e)}")
            return jsonify({'error': str(e)}), 500


    @app.route('/delete_class', methods=['DELETE'])
    def delete_class():
        try:
            stage = session.get('school_stage')
            class_name = request.args.get("class_name")

            if not stage or not class_name:
                return jsonify({'error': 'Missing stage or class name'}), 400

            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                return jsonify({'error': 'Invalid class name'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            try:
                cursor = conn.cursor()

                tables_to_delete = [class_name,
                                    f"{class_name}_notifications",
                                    f"{class_name}_evaluations",
                                    f"{class_name}_videos"]
                for table in tables_to_delete:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                    print(f"Table {table} deleted successfully")

                conn.commit()
                return jsonify({'message': f'Class {class_name} and related tables deleted successfully'}), 200
            finally:
                if conn and conn.is_connected():
                    conn.close()
        except mysql.connector.Error as err:
            logging.error(f"Database Error in delete_class: {err}")
            return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            logging.error(f"Unexpected error in delete_class: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500












    @app.route('/manage_students', methods=['GET'])
    def manage_students():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            try:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES LIKE 'class%'")
                all_tables = [row[0] for row in cursor.fetchall()]
                classes = [table for table in all_tables if not table.endswith(('_evaluations', '_notifications', "_videos"))]

                return render_template('manage_students.html', classes=classes)
            finally:
                conn.close()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return jsonify({'error': f'Database connection failed: {str(err)}'}), 500






    @app.route('/add_student', methods=['POST'])
    def add_student_route():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            student_code = request.form.get('student_code')
            class_name = request.form.get('class_name')
            student_name = request.form.get('student_name')
            student_age = request.form.get('student_age')
            password = request.form.get('password')
            parent_name = request.form.get('parent_name')
            parent_password = request.form.get('parent_password')
            phone_number = request.form.get('phone_number')
            student_photo = request.files.get('student_photo')

            if not all([student_code, class_name, student_name, student_age, password, parent_name, parent_password, student_photo]):
                return jsonify({'error': 'Missing required fields'}), 400

            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                return jsonify({'error': 'Invalid class name'}), 400

            if not student_code.isdigit():
                return jsonify({'error': 'Invalid student code'}), 400

            conn = get_connection_by_stage(stage)
            try:
                success = add_student(conn, student_code, student_name, student_age, class_name, password)
                if not success:
                    return jsonify({'error': 'Failed to add student'}), 500

                parent_success = add_parent(conn, student_code, parent_name, parent_password, phone_number)
                if not parent_success:
                    print("Warning: Failed to add parent information or parent already exists.")

                photo_dir = os.path.join('faces', class_name)
                os.makedirs(photo_dir, exist_ok=True)
                photo_path = os.path.join(photo_dir, f"{student_code}.jpg")
                student_photo.save(photo_path)
                print(f"Student photo saved at {photo_path}")

                return jsonify({'message': f'Student {student_name} added successfully'}), 200
            finally:
                conn.close()
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': 'Server error'}), 500







    @app.route('/student_details', methods=['GET'])
    def student_details():
        try:
            stage = session.get('school_stage')
            class_name = request.args.get("class_name")

            if not stage or not class_name:
                return jsonify({'error': 'Missing school stage or class name'}), 400

            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                return jsonify({'error': 'Invalid class name'}), 400

            conn = get_connection_by_stage(stage)
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT code, name FROM {class_name}")
                students = cursor.fetchall()

                student_list = []
                for student in students:
                    student_code = student[0]

                    cursor.execute(
                        f"SELECT date, evaluation, note FROM {class_name}_evaluations WHERE student_code = %s",
                        (student_code,)
                    )
                    evaluations = [
                        {'date': eval[0], 'evaluation': eval[1], 'note': eval[2]}
                        for eval in cursor.fetchall()
                    ]

                    cursor.execute(
                        "SELECT parent_name, phone_number FROM parents WHERE student_code = %s",
                        (student_code,)
                    )
                    parent_data = cursor.fetchone()
                    parent_info = {
                        'name': parent_data[0] if parent_data and parent_data[0] else 'N/A',
                        'phone': parent_data[1] if parent_data and parent_data[1] else 'N/A'
                    } if parent_data else {'name': 'N/A', 'phone': 'N/A'}

                    student_list.append({
                        'code': student_code,
                        'name': student[1],
                        'evaluations': evaluations,
                        'parent': parent_info
                    })

                return render_template('student_details.html', students=student_list, class_name=class_name, stage=stage)
            finally:
                conn.close()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return jsonify({'error': f'Database connection failed: {str(err)}'}), 500




    @app.route('/delete_student', methods=['POST'])
    def delete_student_route():
        try:
            stage = session.get('school_stage')
            class_name = request.form.get("class_name")
            student_code = request.form.get("student_code")

            if not stage or not class_name or not student_code:
                return jsonify({'error': 'Missing stage, class name, or student code'}), 400

            if not student_code.isdigit():
                return jsonify({'error': 'Invalid student code'}), 400

            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                return jsonify({'error': 'Invalid class name'}), 400

            conn = get_connection_by_stage(stage)
            try:
                cursor = conn.cursor()

                cursor.execute(f"DELETE FROM {class_name} WHERE code = %s", (student_code,))
                cursor.execute(f"DELETE FROM {class_name}_evaluations WHERE student_code = %s", (student_code,))
                conn.commit()

                photo_path = os.path.join('faces', class_name, f"{student_code}.jpg")
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    print(f"Student photo deleted at {photo_path}")

                return redirect(url_for('student_details', class_name=class_name))
            finally:
                conn.close()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return jsonify({'error': f'Database connection failed: {str(err)}'}), 500








    @app.route('/manage_teachers', methods=['GET'])
    def manage_teachers():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            try:
                teachers = get_teachers2(conn)
                return render_template('manage_teachers.html', teachers=teachers)
            finally:
                conn.close()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return jsonify({'error': f'Database connection failed: {str(err)}'}), 500




 


    @app.route('/update_teacher_classes', methods=['POST'])
    def update_teacher_classes():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not found in session'}), 400

            data = request.get_json()
            teacher_code = data.get('teacher_code')
            accessible_classes_json = data.get('accessible_classes')

            if not teacher_code or accessible_classes_json is None:
                return jsonify({'error': 'Missing teacher code or accessible classes'}), 400

            try:
                accessible_classes_list = json.loads(accessible_classes_json)
                if not isinstance(accessible_classes_list, list):
                    raise ValueError("Accessible classes must be a list")
            except Exception as e:
                print(f"Error parsing accessible_classes: {e}")
                return jsonify({'error': 'Invalid accessible classes format'}), 400

            accessible_classes_str = json.dumps(accessible_classes_list)

            conn = get_connection_by_stage(stage)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE teachers SET accessible_classes = %s WHERE code = %s",
                    (accessible_classes_str, teacher_code)
                )
                conn.commit()
                return jsonify({'message': 'Accessible classes updated successfully'}), 200
            finally:
                conn.close()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return jsonify({'error': f'Database connection failed: {str(err)}'}), 500







    @app.route('/add_teacher', methods=['POST'])
    def add_teacher_route():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not found in session'}), 400

            teacher_code = request.form.get('teacher_code')
            teacher_name = request.form.get('teacher_name')
            accessible_classes = request.form.get('accessible_classes') 
            teacher_password = request.form.get('teacher_password')

            if not all([teacher_code, teacher_name, accessible_classes, teacher_password]):
                return jsonify({'error': 'Missing required fields'}), 400

            try:
                accessible_classes_list = json.loads(accessible_classes)
                if not isinstance(accessible_classes_list, list):
                    raise ValueError("Accessible classes must be a list")
            except Exception as e:
                print(f"Error parsing accessible_classes: {e}")
                return jsonify({'error': 'Invalid accessible classes format'}), 400

            accessible_classes_str = json.dumps(accessible_classes_list)

            conn = get_connection_by_stage(stage)
            try:
                success = add_teacher(conn, teacher_name, accessible_classes_str, teacher_password, teacher_code)
                if not success:
                    return jsonify({'error': 'Failed to add teacher'}), 500

                return jsonify({'message': f'Teacher {teacher_name} added successfully'}), 200
            finally:
                conn.close()

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': 'Server error'}), 500









    @app.route('/manage_subjects', methods=['GET', 'POST'])
    def manage_subjects():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            flash_message = None
            flash_type = None

            if request.method == 'POST':
                if 'add_subject' in request.form:
                    new_subject_name = request.form.get('subject_name')
                    if new_subject_name and re.match(r'^[a-zA-Z0-9_]+$', new_subject_name):
                        try:
                            cursor_check = conn.cursor()
                            cursor_check.execute("SELECT name FROM subjects WHERE name = %s", (new_subject_name,))
                            if cursor_check.fetchone():
                                flash_message = f"Subject '{new_subject_name}' already exists."
                                flash_type = "warning"
                            else:
                                success = add_subject_with_teacher_table(conn, new_subject_name)
                                if success:
                                    flash_message = f"Subject '{new_subject_name}' added successfully."
                                    flash_type = "success"
                                else:
                                    flash_message = f"Failed to add subject '{new_subject_name}'."
                                    flash_type = "danger"
                        except mysql.connector.Error as db_err:
                            logging.error(f"Database error adding subject: {db_err}")
                            flash_message = "Database error occurred while adding subject."
                            flash_type = "danger"
                        finally:
                            if 'cursor_check' in locals() and cursor_check:
                                cursor_check.close()
                    else:
                        flash_message = "Invalid subject name format."
                        flash_type = "danger"

                elif 'delete_subject' in request.form:
                    subject_to_delete = request.form.get('subject_to_delete')
                    if subject_to_delete and re.match(r'^[a-zA-Z0-9_]+$', subject_to_delete):
                        try:
                            success = delete_subject(conn, subject_to_delete)
                            if success:
                                flash_message = f"Subject '{subject_to_delete}' deleted successfully."
                                flash_type = "success"
                            else:
                                flash_message = f"Failed to delete subject '{subject_to_delete}'."
                                flash_type = "danger"
                        except mysql.connector.Error as db_err:
                            logging.error(f"Database error deleting subject: {db_err}")
                            flash_message = "Database error occurred while deleting subject."
                            flash_type = "danger"
                    else:
                        flash_message = "Invalid subject name format for deletion."
                        flash_type = "danger"

            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT name FROM subjects")
                subjects_raw = cursor.fetchall()
                subjects_list = [s['name'] for s in subjects_raw]

                subjects_with_teachers = {}
                for subject_name in subjects_list:
                    if not re.match(r'^[a-zA-Z0-9_]+$', subject_name):
                        subjects_with_teachers[subject_name] = ["Invalid subject name format"]
                        continue

                    try:
                        cursor.execute(f"SELECT teacher_code FROM `{subject_name}`")
                        teacher_codes_raw = cursor.fetchall()
                        teacher_codes = [str(t['teacher_code']) for t in teacher_codes_raw]

                        if teacher_codes:
                            format_strings = ','.join(['%s'] * len(teacher_codes))
                            query_teachers = f"SELECT name FROM teachers WHERE code IN ({format_strings})"
                            cursor.execute(query_teachers, tuple(teacher_codes))
                            teacher_names_raw = cursor.fetchall()
                            teacher_names = [t['name'] for t in teacher_names_raw]
                        else:
                            teacher_names = []

                        subjects_with_teachers[subject_name] = teacher_names
                    except mysql.connector.Error as e:
                        logging.error(f"Error fetching teachers for subject {subject_name}: {e}")
                        subjects_with_teachers[subject_name] = ["Error fetching teachers"]
            finally:
                cursor.close()

            return render_template('manage_subjects.html',
                                subjects_with_teachers=subjects_with_teachers,
                                stage=stage,
                                flash_message=flash_message,
                                flash_type=flash_type)

        except mysql.connector.Error as err:
            logging.error(f"Database Error in manage_subjects: {err}")
            return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            logging.error(f"General Error in manage_subjects: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
        finally:
            if 'conn' in locals() and conn and conn.is_connected():
                conn.close()








    @app.route('/assign_teachers_to_subjects', methods=['GET', 'POST'])
    def assign_teachers_to_subjects():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            flash_message = None
            flash_type = None

            if request.method == 'POST':
               
                if 'subject_name' in request.form and 'teacher_code' in request.form:
                    subject_name = request.form.get('subject_name')
                    teacher_code_to_add = request.form.get('teacher_code')
                    action = request.form.get('action')


                    if not subject_name or not teacher_code_to_add:
                        flash_message = "Subject and Teacher must be selected."
                        flash_type = "warning"
                    elif not re.match(r'^[a-zA-Z0-9_]+$', subject_name):
                        flash_message = "Invalid subject name format."
                        flash_type = "danger"
                    elif not teacher_code_to_add.isdigit():
                        flash_message = "Invalid teacher code format."
                        flash_type = "danger"
                    else:
                        try:
                            cursor = conn.cursor()
                            if action == 'add':
                                if not re.match(r'^[a-zA-Z0-9_]+$', subject_name):
                                    raise ValueError("Invalid subject name format for database query")
                                cursor.execute(f"SELECT teacher_code FROM `{subject_name}` WHERE teacher_code = %s", (teacher_code_to_add,))
                                existing_teacher = cursor.fetchone()

                                if existing_teacher:
                                    flash_message = f"Teacher is already assigned to {subject_name}."
                                    flash_type = "warning"
                                else:
                                    cursor.execute(f"INSERT INTO `{subject_name}` (teacher_code) VALUES (%s)", (teacher_code_to_add,))
                                    conn.commit()
                                    flash_message = f"Teacher assigned to {subject_name} successfully."
                                    flash_type = "success"
                            elif action == 'remove':
                                if not re.match(r'^[a-zA-Z0-9_]+$', subject_name):
                                    raise ValueError("Invalid subject name format for database query")
                                cursor.execute(f"DELETE FROM `{subject_name}` WHERE teacher_code = %s", (teacher_code_to_add,))
                                conn.commit()
                                if cursor.rowcount > 0:
                                    flash_message = f"Teacher removed from {subject_name} successfully."
                                    flash_type = "success"
                                else:
                                    flash_message = f"Teacher was not assigned to {subject_name}."
                                    flash_type = "warning"
                        except (mysql.connector.Error, ValueError) as db_err:
                            conn.rollback()
                            logging.error(f"DB Error in assign_teachers_to_subjects: {db_err}")
                            flash_message = "Database error or invalid input occurred."
                            flash_type = "danger"
                        finally:
                            if 'cursor' in locals() and cursor:
                                cursor.close()

            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT name FROM subjects")
                subjects_raw = cursor.fetchall()
                subjects_list = [s['name'] for s in subjects_raw]

                subjects_with_teachers_detailed = {}
                cursor.execute("SELECT code, name FROM teachers")
                all_teachers_raw = cursor.fetchall()
                all_teachers_dict = {str(t['code']): t['name'] for t in all_teachers_raw}

                for subject_name in subjects_list:
                    if not re.match(r'^[a-zA-Z0-9_]+$', subject_name):
                        subjects_with_teachers_detailed[subject_name] = [{"code": "N/A", "name": "Invalid subject name format"}]
                        continue

                    try:
                        cursor.execute(f"SELECT teacher_code FROM `{subject_name}`")
                        teacher_codes_raw = cursor.fetchall()
                        teacher_codes = [str(t['teacher_code']) for t in teacher_codes_raw]

                        teacher_details = []
                        for code in teacher_codes:
                            name = all_teachers_dict.get(code, f"Unknown (Code: {code})")
                            teacher_details.append({'code': code, 'name': name})

                        subjects_with_teachers_detailed[subject_name] = teacher_details
                    except mysql.connector.Error as e:
                        logging.error(f"Error fetching teachers for subject {subject_name}: {e}")
                        subjects_with_teachers_detailed[subject_name] = [{"code": "N/A", "name": "Error fetching teachers"}]
            finally:
                cursor.close()

            return render_template('assign_teachers_to_subjects.html',
                                subjects_with_teachers=subjects_with_teachers_detailed,
                                all_teachers=all_teachers_dict,
                                subjects_list=subjects_list,
                                stage=stage,
                                flash_message=flash_message,
                                flash_type=flash_type)

        except mysql.connector.Error as err:
            logging.error(f"Database Error in assign_teachers_to_subjects: {err}")
            return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            logging.error(f"General Error in assign_teachers_to_subjects: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
        finally:
            if 'conn' in locals() and conn and conn.is_connected():
                conn.close()








    @app.route('/browse_videos', methods=['GET'])
    def browse_videos():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            try:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES LIKE 'class%'")
                all_tables = [row[0] for row in cursor.fetchall()]
                class_names = [table for table in all_tables if not table.endswith(('_evaluations', '_notifications', '_videos'))]

                selected_class = request.args.get('class_name')
                if selected_class and not re.match(r'^[a-zA-Z0-9_]+$', selected_class):
                    logging.error(f"Invalid class name format in browse_videos: {selected_class}")
                    return jsonify({'error': 'Invalid class name format'}), 400

                videos_by_subject = {}

                if selected_class and selected_class in class_names:
                    if not re.match(r'^[a-zA-Z0-9_]+$', selected_class):
                        raise ValueError("Invalid class name format for database query")
                    cursor.execute(f"SELECT id, link, subject, title FROM {selected_class}_videos ORDER BY subject, title")
                    videos = cursor.fetchall()
                    for video in videos:
                        subject = video[2]
                        if subject not in videos_by_subject:
                            videos_by_subject[subject] = []
                        videos_by_subject[subject].append({
                            'id': video[0],
                            'link': video[1],
                            'subject': video[2],
                            'title': video[3]
                        })

                return render_template('browse_videos.html',
                                    class_names=class_names,
                                    selected_class=selected_class,
                                    videos_by_subject=videos_by_subject,
                                    stage=stage)

            finally:
                if conn and conn.is_connected():
                    conn.close()

        except (mysql.connector.Error, ValueError) as err:
            logging.error(f"Database/Error in browse_videos: {err}")
            return jsonify({'error': 'Database connection failed or invalid input'}), 500
        except Exception as e:
            logging.error(f"General Error in browse_videos: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500




    @app.route('/manage_parent_notifications', methods=['GET', 'POST'])
    def manage_parent_notifications():
        try:
            stage = session.get('school_stage')
            code = session.get('headteacher_code')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            conn = get_connection_by_stage(stage)
            if not conn:
                return jsonify({'error': 'Invalid school stage'}), 400

            flash_message = None
            flash_type = None

            if request.method == 'POST':
                if 'add_notification' in request.form:
                    title = request.form.get('title')
                    notification = request.form.get('notification')
                    notes = request.form.get('notes')

                    title_clean = bleach.clean(title) if title else None
                    notification_clean = bleach.clean(notification) if notification else None
                    notes_clean = bleach.clean(notes) if notes else None

                    if not all([title_clean, notification_clean]):
                        flash_message = "Title and notification are required."
                        flash_type = "warning"
                    else:
                        try:
                            success = add_parent_notification(conn, title_clean, notification_clean, notes_clean)
                            conn.commit()   
                            if success:
                                flash_message = "Parent notification added successfully."
                                flash_type = "success"
                            else:
                                flash_message = "Failed to add parent notification."
                                flash_type = "danger"
                        except mysql.connector.Error as db_err:
                            logging.error(f"Database error adding parent notification: {db_err}")
                            flash_message = "Database error occurred while adding notification."
                            flash_type = "danger"

                elif 'delete_notification' in request.form:
                    notification_id = request.form.get('notification_id')
                    if notification_id and notification_id.isdigit():
                        try:
                            success = delete_parent_notification(conn, notification_id)
                            conn.commit()   
                            if success:
                                flash_message = "Parent notification deleted successfully."
                                flash_type = "success"
                            else:
                                flash_message = "Failed to delete parent notification."
                                flash_type = "danger"
                        except mysql.connector.Error as db_err:
                            logging.error(f"Database error deleting parent notification: {db_err}")
                            flash_message = "Database error occurred while deleting notification."
                            flash_type = "danger"
                    else:
                        flash_message = "Invalid notification ID."
                        flash_type = "danger"

                return redirect(url_for('manage_parent_notifications'))

            try:
                parent_notifications = fetch_all_parents_notifications(conn)
            except mysql.connector.Error as db_err:
                logging.error(f"Database error fetching parent notifications: {db_err}")
                parent_notifications = []
                flash_message = flash_message or "Error fetching notifications."
                flash_type = flash_type or "danger"

            return render_template('manage_parent_notifications.html',
                                code=code,
                                notifications=parent_notifications,
                                stage=stage,
                                flash_message=flash_message,
                                flash_type=flash_type)

        except mysql.connector.Error as err:
            logging.error(f"Database Error in manage_parent_notifications: {err}")
            return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            logging.error(f"General Error in manage_parent_notifications: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
        finally:
            if 'conn' in locals() and conn and conn.is_connected():
                conn.close()







    @app.route('/manage_system', methods=['GET'])
    def manage_system():
        stage = session.get('school_stage')
        if not stage:
            return jsonify({'error': 'School stage not provided'}), 400

        try:
            system_status = "Running" if is_running() else "Stopped"
            return render_template('manage_system.html', stage=stage, system_status=system_status)
        except RuntimeError as e:
            logging.error(f"Runtime error in manage_system: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logging.error(f"Unexpected error in manage_system: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500


    @app.route('/start_system', methods=['POST'])
    def start_system_route():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            if is_running():
                return jsonify({'message': 'System is already running'}), 200

            start_system()
            logging.info("System started successfully.")
            return jsonify({'message': 'System started successfully'}), 200

        except Exception as e:
            logging.error(f"Error in start_system: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500


    @app.route('/stop_system', methods=['POST'])
    def stop_system_route():
        try:
            stage = session.get('school_stage')
            if not stage:
                return jsonify({'error': 'School stage not provided'}), 400

            logging.info("Attempting to stop the system...")
            stop_system()
            logging.info("System stopped successfully.")
            return jsonify({'message': 'System stopped successfully'}), 200

        except Exception as e:
            logging.error(f"Error in stop_system: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500







    @app.route('/parent_login', methods=['POST'])
    def parent_login():
        if request.method == 'POST':
            school_stage = request.form.get('school_stage') or session.get('school_stage')
            grade = request.form.get('student_grade')
            class_number = request.form.get('student_class_num')
            student_code = request.form.get('student_code')
            parent_password = request.form.get('parent_password')

            if not all([school_stage, grade, class_number, student_code, parent_password]):
                return jsonify({"error": "Missing required fields"}), 400

            if not re.match(r'^[a-zA-Z]+$', school_stage):
                return jsonify({"error": "Invalid school stage format"}), 400
            if not grade.isdigit() or not class_number.isdigit() or not student_code.isdigit():
                return jsonify({"error": "Invalid numeric input format"}), 400

            conn = get_connection_by_stage(school_stage)
            if conn:
                try:
                    try:
                        student_code_int = int(student_code)
                    except ValueError:
                        return jsonify({"error": "Invalid student code format"}), 400

                    result = get_parent_data(conn, student_code_int, parent_password)

                    if isinstance(result, tuple):
                        error_data, status_code = result
                        if status_code == 401:
                            return render_template('parent.html', error=bleach.clean(error_data.get('error', 'Invalid credentials')))
                        return jsonify(error_data), status_code

                    parent_data = result
                    student_data = parent_data.get('student_data')
                    student_class = parent_data.get('student_class')

                    if not student_data or not student_class:
                        return jsonify({"error": "Incomplete data from parent lookup"}), 500

                    session['user_type'] = 'parent'
                    session['parent_id'] = parent_data.get('id') 
                    session['student_code'] = student_code
                    session['school_stage'] = school_stage
                    session['student_class'] = student_class

                    return render_template(
                        'parent_dashboard.html',
                        parent_name=bleach.clean(parent_data['parent_name']),
                        student=student_data,
                        class_name=bleach.clean(student_class),
                        school_stage=bleach.clean(school_stage)
                    )

                except mysql.connector.Error as db_err:
                    logging.error(f"Database error in parent_login: {db_err}")
                    return render_template('parent.html', error=bleach.clean("Database connection error."))
                except Exception as e:
                    logging.error(f"Unexpected error in parent_login: {e}")
                    return render_template('parent.html', error=bleach.clean("An unexpected error occurred."))
                finally:
                    if conn and conn.is_connected():
                        conn.close()
            return render_template('parent.html', error=bleach.clean("Invalid school stage."))
        return jsonify({"error": "Method not allowed"}), 405








    @app.route('/parent/dashboard')
    def parent_dashboard():
        school_stage = session.get('school_stage')
        student_code = session.get('student_code')
        class_name = session.get('student_class') 

        if not all([school_stage, student_code, class_name]):
            return redirect(url_for('index')) 

        try:
            student_code_int = int(student_code)
        except (ValueError, TypeError):
            session.clear() 
            return redirect(url_for('index'))

        conn = get_connection_by_stage(school_stage)
        if not conn:
            session.clear()
            return redirect(url_for('index'))

        try:
            student_data = get_student_data(conn, class_name, student_code_int)
            if isinstance(student_data, tuple):
                error_data, status_code = student_data
                if status_code != 200:
                    print(f"Error fetching student data: {error_data}")
                    session.clear()
                    return redirect(url_for('index'))

            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT parent_name FROM parents WHERE student_code = %s", (student_code_int,))
                parent_res = cursor.fetchone()
            finally:
                cursor.close()

            if not parent_res:
                print("Parent data not found for student.")
                session.clear()
                return redirect(url_for('index'))

            parent_name = parent_res['parent_name']

            return render_template(
                'parent_dashboard.html',
                parent_name=bleach.clean(parent_name),
                student=student_data,
                class_name=bleach.clean(class_name),
                school_stage=bleach.clean(school_stage)
            )

        except Exception as e:
            logging.error(f"Error in parent_dashboard route: {e}")
            session.clear() 
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                conn.close()







    @app.route('/parent/attendance')
    def parent_attendance():
        student_code = session.get('student_code')
        school_stage = session.get('school_stage')
        class_name = session.get('student_class')

        if not all([student_code, school_stage, class_name]):
            return redirect(url_for('index'))

        conn = get_connection_by_stage(school_stage)
        if not conn:
            session.clear() 
            return redirect(url_for('index'))

        try:
            student_code_int = int(student_code)
            student_data = get_student_data(conn, class_name, student_code_int)
            
            if isinstance(student_data, tuple):
                error_data, status_code = student_data
                if status_code != 200:
                    print(f"Error fetching student data: {error_data}")
                    session.clear()
                    return redirect(url_for('index'))

            attendance_schedule = process_attendance_data(student_data)

            return render_template(
                'parent_attendance.html',
                student=student_data,
                schedule=attendance_schedule,
                class_name=bleach.clean(class_name),
                school_stage=bleach.clean(school_stage)
            )
        except ValueError:
            session.clear()
            return redirect(url_for('index'))
        except Exception as e:
            logging.error(f"Error in parent_attendance: {e}")
            session.clear() 
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                conn.close()




    @app.route('/parent/evaluations')
    def parent_evaluations():
        student_code = session.get('student_code')
        school_stage = session.get('school_stage')
        class_name = session.get('student_class')

        if not all([student_code, school_stage, class_name]):
            return redirect(url_for('index'))

        conn = get_connection_by_stage(school_stage)
        if not conn:
            session.clear()
            return redirect(url_for('index'))

        try:
            student_code_int = int(student_code)
            evaluations = get_student_evaluations(conn, class_name, student_code_int)

            student_data = get_student_data(conn, class_name, student_code_int)
            if isinstance(student_data, tuple):
                error_data, status_code = student_data
                if status_code != 200:
                    print(f"Error fetching student data: {error_data}")
                    session.clear()
                    return redirect(url_for('index'))
                else:
                    student_data = {"name": "Unknown", "code": student_code_int}

            return render_template(
                'parent_evaluations.html',
                student=student_data,
                evaluations=evaluations,
                class_name=bleach.clean(class_name),
                school_stage=bleach.clean(school_stage)
            )
        except ValueError:
            session.clear()
            return redirect(url_for('index'))
        except Exception as e:
            logging.error(f"Error in parent_evaluations: {e}")
            session.clear() 
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                conn.close()




    @app.route('/parent/class_notifications')
    def parent_class_notifications():
        student_code = session.get('student_code')
        school_stage = session.get('school_stage')
        class_name = session.get('student_class')

        if not all([student_code, school_stage, class_name]):
            return redirect(url_for('index'))

        conn = get_connection_by_stage(school_stage)
        if not conn:
            session.clear() 
            return redirect(url_for('index'))

        try:
            class_notifications = fetch_all_notifications(conn, class_name)

            student_code_int = int(student_code)
            student_data = get_student_data(conn, class_name, student_code_int)
            if isinstance(student_data, tuple):
                error_data, status_code = student_data
                if status_code != 200:
                    print(f"Error fetching student data: {error_data}")
                    session.clear()
                    return redirect(url_for('index'))
                else:
                    student_data = {"name": "Unknown", "code": student_code_int}

            return render_template(
                'parent_class_notifications.html',
                student=student_data,
                class_notifications=class_notifications,
                class_name=bleach.clean(class_name),
                school_stage=bleach.clean(school_stage)
            )
        except ValueError:
            session.clear()
            return redirect(url_for('index'))
        except Exception as e:
            logging.error(f"Error in parent_class_notifications: {e}")
            session.clear() 
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                conn.close()







    @app.route('/parent/notifications')
    def parent_notifications():
        student_code = session.get('student_code')
        school_stage = session.get('school_stage')
        class_name = session.get('student_class')

        if not all([student_code, school_stage, class_name]):
            return redirect(url_for('index'))

        conn = get_connection_by_stage(school_stage)
        if not conn:
            session.clear() 
            return redirect(url_for('index'))

        try:
            notifications = fetch_all_parents_notifications(conn)
            return render_template(
                'parent_notifications.html',
                notifications=notifications,
                class_name=bleach.clean(class_name),
                school_stage=bleach.clean(school_stage),
                student_code=student_code 
            )
        except Exception as e:
            logging.error(f"Error in parent_notifications: {e}")
            session.clear()
            return redirect(url_for('index'))
        finally:
            if conn and conn.is_connected():
                conn.close()


 




    @app.route('/chats', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def chats():
        if 'user_type' not in session or not session['user_type']:
            return redirect(url_for('index'))
        
        user_type = session['user_type']
        school_stage = session.get('school_stage')
        conn = get_connection_by_stage(school_stage)
        if not conn:
            return jsonify({"error": "Invalid school stage"}), 400
        
        existing_conversations = []
        available_contacts = []
        
        if user_type == 'student':
            class_name = session.get('class_name')

            print (class_name)
            student_code = session.get('student_code')
            
            if not class_name or not student_code:
                return jsonify({"error": "Missing student data"}), 400
            
            students = my_students(class_name, conn)
            for code, name in students.items():
                if int(code) != int(student_code): 
                    contact = {
                        'name': bleach.clean(name),
                        'code': bleach.clean(str(code)),
                        'type': 'student'
                    }
                    messages = get_messages_for_user(conn, student_code, 'student', code, 'student')
                    if messages:
                        last_message = messages[-1]
                        existing_conversations.append({
                            'contact_name': contact['name'],
                            'contact_code': contact['code'],
                            'contact_type': 'student',
                            'last_message': bleach.clean(last_message['message']),
                            'created_at': last_message['created_at']
                        })
                    available_contacts.append(contact)
            
            cursor = conn.cursor(dictionary=True)
            try:
                query = "SELECT code, name, accessible_classes FROM teachers"
                cursor.execute(query)
                teachers = cursor.fetchall()
                
                for teacher in teachers:
                    raw_classes = teacher['accessible_classes']
                    if raw_classes:
                        cleaned_classes = re.sub(r'[\[\]\s\'"]', '', raw_classes).strip()
                        try:
                            classes_list = json.loads(raw_classes)
                        except json.JSONDecodeError:
                            classes_list = [cls.strip() for cls in cleaned_classes.split(',') if cls.strip()]
                        
                        if class_name in classes_list:
                            contact = {
                                'name': bleach.clean(teacher['name']),
                                'code': bleach.clean(str(teacher['code'])),
                                'type': 'teacher'
                            }
                            messages = get_messages_for_user(conn, student_code, 'student', teacher['code'], 'teacher')
                            if messages:
                                last_message = messages[-1]
                                existing_conversations.append({
                                    'contact_name': contact['name'],
                                    'contact_code': contact['code'],
                                    'contact_type': 'teacher',
                                    'last_message': bleach.clean(last_message['message']),
                                    'created_at': last_message['created_at']
                                })
                            available_contacts.append(contact)
            except mysql.connector.Error as err:
                return jsonify({"error": str(err)}), 500
            finally:
                cursor.close()
                if conn.is_connected():
                    conn.close()
            
            existing_conversations.sort(key=lambda x: x['created_at'], reverse=True)
            
            return render_template('chats.html', 
                                existing_conversations=existing_conversations, 
                                available_contacts=available_contacts)
        
        elif user_type == 'teacher':
            teacher_code = session.get('teacher_code')
            if not teacher_code:
                logging.error("Missing teacher_code in session")
                return jsonify({"error": "Missing session data"}), 400
            
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT accessible_classes FROM teachers WHERE code = %s"
                cursor.execute(query, (teacher_code,))
                res = cursor.fetchone()
                if not res or not res['accessible_classes']:
                    logging.error(f"No accessible classes for teacher {teacher_code}")
                    return render_template('chats.html', existing_conversations=[], available_contacts=[])
                
                try:
                    accessible_classes = json.loads(res['accessible_classes'])
                except json.JSONDecodeError:
                    cleaned = re.sub(r'[\[\]\s\'"]', '', res['accessible_classes']).strip()
                    accessible_classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
                
                for class_name in accessible_classes:
                    students = my_students(class_name, conn)
                    logging.debug(f"Fetched students for class {class_name}: {students}")
                    for code, name in students.items():
                        contact = {'name': bleach.clean(name), 'code': code, 'type': 'student'}
                        available_contacts.append(contact)
                        messages = get_messages_for_user(conn, teacher_code, 'teacher', code, 'student')
                        if messages:
                            last_message = messages[-1]
                            existing_conversations.append({
                                'contact_name': contact['name'],
                                'contact_code': contact['code'],
                                'contact_type': 'student',
                                'last_message': bleach.clean(last_message['message']),
                                'created_at': last_message['created_at']
                            })
                
                cursor.execute("SELECT id, parent_name, student_code FROM parents")
                all_parents = cursor.fetchall()
                logging.debug(f"Fetched {len(all_parents)} parents from parents table")

                teacher_student_codes = set()
                for cls in accessible_classes:
                    try:
                        students = my_students(cls, conn)
                        teacher_student_codes.update(int(code) for code in students.keys())
                    except Exception as e:
                        logging.error(f"Error getting students for class {cls}: {e}")
                        continue

                for parent in all_parents:
                    if parent['student_code'] is not None and parent['student_code'] in teacher_student_codes:
                        contact = {
                            'name': bleach.clean(parent['parent_name']),
                            'code': parent['student_code'],  
                            'type': 'parent'
                        }
                        logging.debug(f"Added parent {parent['parent_name']} for student_code {parent['student_code']}")
                        available_contacts.append(contact)
                        
                        messages = get_messages_for_user(conn, teacher_code, 'teacher', parent['student_code'], 'parent')
                        if messages:
                            last_message = messages[-1]
                            existing_conversations.append({
                                'contact_name': contact['name'],
                                'contact_code': contact['code'],
                                'contact_type': 'parent',
                                'last_message': bleach.clean(last_message['message']),
                                'created_at': last_message['created_at']
                            })
                
                shared_teachers = get_teachers_with_shared_classes(teacher_code, conn)
                logging.debug(f"Fetched {len(shared_teachers)} shared teachers for teacher {teacher_code}")
                for teacher in shared_teachers:
                    available_contacts.append(teacher)
                    messages = get_messages_for_user(conn, teacher_code, 'teacher', teacher['code'], 'teacher')
                    if messages:
                        last_message = messages[-1]
                        existing_conversations.append({
                            'contact_name': teacher['name'],
                            'contact_code': teacher['code'],
                            'contact_type': 'teacher',
                            'last_message': bleach.clean(last_message['message']),
                            'created_at': last_message['created_at']
                        })
                
                headteacher = get_headteacher_data(conn)
                if headteacher:
                    logging.debug(f"Added headteacher {headteacher['name']}")
                    available_contacts.append(headteacher)
                    messages = get_messages_for_user(conn, teacher_code, 'teacher', headteacher['code'], 'headteacher')
                    if messages:
                        last_message = messages[-1]
                        existing_conversations.append({
                            'contact_name': headteacher['name'],
                            'contact_code': headteacher['code'],
                            'contact_type': 'headteacher',
                            'last_message': bleach.clean(last_message['message']),
                            'created_at': last_message['created_at']
                        })
                
                existing_conversations.sort(key=lambda x: x['created_at'], reverse=True)
                logging.info(f"Chats loaded successfully for teacher {teacher_code} with {len(available_contacts)} contacts")
                return render_template('chats.html', existing_conversations=existing_conversations, available_contacts=available_contacts)
            except mysql.connector.Error as err:
                logging.error(f"Database error in chats for teacher: {str(err)}")
                return jsonify({"error": str(err)}), 500
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if conn.is_connected():
                    conn.close()
      
        
        elif user_type == 'headteacher':
            headteacher_code = session.get('headteacher_code')
            if not headteacher_code:
                logging.error("Missing headteacher_code in session")
                flash("Missing session data", "error")
                return redirect(url_for('headteacher_dashboard_page'))
            
            existing_conversations = []
            available_contacts = []
            
            try:
                with conn.cursor(dictionary=True) as cursor:
                    query = """
                        SELECT DISTINCT m.sender_id, m.sender_type, m.receiver_id, m.receiver_type,
                            CASE 
                                WHEN m.sender_type = 'teacher' THEN t.name
                                WHEN m.receiver_type = 'teacher' THEN t.name
                            END AS contact_name,
                            m.message AS last_message,
                            m.created_at
                        FROM messages m
                        LEFT JOIN teachers t ON 
                            (m.sender_type = 'teacher' AND m.sender_id = t.code) OR 
                            (m.receiver_type = 'teacher' AND m.receiver_id = t.code)
                        WHERE (m.sender_id = %s AND m.sender_type = 'headteacher') OR 
                            (m.receiver_id = %s AND m.receiver_type = 'headteacher')
                        ORDER BY m.created_at DESC
                    """
                    cursor.execute(query, (headteacher_code, headteacher_code))
                    conversations = cursor.fetchall()
                    
                    for conv in conversations:
                        if conv['sender_id'] == headteacher_code and conv['sender_type'] == 'headteacher':
                            contact_id = conv['receiver_id']
                            contact_type = conv['receiver_type']
                        else:
                            contact_id = conv['sender_id']
                            contact_type = conv['sender_type']
                        
                        if contact_type != 'teacher':
                            logging.warning(f"Skipping invalid contact_type {contact_type} for headteacher {headteacher_code}")
                            continue
                        
                        if contact_id is None or str(contact_id).strip() == '':
                            logging.warning(f"Skipping invalid contact_id in conversation: {conv}")
                            continue
                        
                        existing_conversations.append({
                            'contact_code': contact_id,
                            'contact_type': contact_type,
                            'contact_name': bleach.clean(conv['contact_name']) if conv['contact_name'] else 'Unknown',
                            'last_message': bleach.clean(conv['last_message']),
                            'created_at': conv['created_at']
                        })
                    
                teachers = get_teachers_for_headteacher(conn)
                for teacher in teachers:
                    if teacher['code'] and str(teacher['code']).strip() != '':
                        available_contacts.append(teacher)
                    else:
                        logging.warning(f"Skipping teacher with invalid code: {teacher}")
                
                existing_conversations.sort(key=lambda x: x['created_at'], reverse=True)
                print(existing_conversations)
                
                logging.info(f"Chats loaded successfully for headteacher {headteacher_code} with {len(available_contacts)} contacts")
                return render_template('chats.html', 
                                    existing_conversations=existing_conversations, 
                                    available_contacts=available_contacts)
            
            except mysql.connector.Error as err:
                logging.error(f"Database error in chats for headteacher: {str(err)}")
                flash("Database error occurred", "error")
                return redirect(url_for('headteacher_dashboard_page'))
            finally:
                if conn.is_connected():
                    conn.close()

        




        
        elif user_type == 'parent':
            student_code = session.get('student_code')
            
            if not student_code:
                logging.error("Missing student_code in session for parent")
                return jsonify({"error": "Missing session data"}), 400
            
            try:
                existing_conversations = get_existing_conversations_for_parent(student_code, conn)
                
                available_teachers = get_teachers_for_parent(student_code, conn)
                available_contacts = available_teachers
                
                existing_conversations.sort(key=lambda x: x['created_at'], reverse=True)
                
                logging.info(f"Chats loaded successfully for parent of student {student_code} with {len(available_contacts)} contacts")
                return render_template('chats.html', 
                                    existing_conversations=existing_conversations, 
                                    available_contacts=available_contacts)
            
            except mysql.connector.Error as err:
                logging.error(f"Database error in chats for parent: {str(err)}")
                return jsonify({"error": str(err)}), 500












         







    @app.route('/chat_room/<contact_code>/<contact_type>', methods=['GET'])
    @limiter.limit(LIMIT)
    def chat_room(contact_code, contact_type):
        print (contact_type)
        user_type = session.get('user_type')
        school_stage = session.get('school_stage')
        if not user_type or not school_stage:
            logging.error(f"Missing session data: user_type={user_type}, school_stage={school_stage}")
            flash("Please log in first", "error")
            return redirect(url_for('index'))

        valid_types = ['student', 'teacher', 'parent', 'headteacher']   
        if contact_type not in valid_types:
            print (contact_type)
            logging.error(f"Invalid contact type: {contact_type} for user_type={user_type}")
            return jsonify({"error": "Invalid contact type"}), 400

        try:
            contact_code = int(contact_code)
        except ValueError:
            logging.error(f"Invalid contact code: {contact_code} for user_type={user_type}")
            return jsonify({"error": "Invalid contact code"}), 400

        conn = get_connection_by_stage(school_stage)
        if not conn:
            logging.error(f"Invalid school stage: {school_stage} for user_type={user_type}")
            return jsonify({"error": "Invalid school stage"}), 400

        contact_name = None
        messages = []

        try:
            if user_type == 'student':
                student_code = session.get('student_code')
                class_name = session.get('class_name')
                if not student_code or not class_name:
                    logging.error(f"Missing student data: student_code={student_code}, class_name={class_name}")
                    return jsonify({"error": "Missing session data"}), 400

                with conn.cursor(dictionary=True) as cursor:
                    if contact_type == 'student':
                        student_data = get_student_data(conn, class_name, contact_code)
                        if isinstance(student_data, tuple):
                            logging.error(f"Error fetching student data: {student_data[0]['error']}")
                            return jsonify({"error": student_data[0]['error']}), student_data[1]
                        contact_name = bleach.clean(student_data.get('name', 'Unknown Student'))
                    elif contact_type == 'teacher':
                        query = "SELECT name, accessible_classes FROM teachers WHERE code = %s"
                        cursor.execute(query, (contact_code,))
                        teacher = cursor.fetchone()
                        if not teacher:
                            logging.error(f"Teacher not found for code: {contact_code}")
                            return jsonify({"error": "Teacher not found"}), 404
                        try:
                            classes_list = json.loads(teacher['accessible_classes'])
                        except json.JSONDecodeError:
                            cleaned = re.sub(r'[\[\]\s\'"]', '', teacher['accessible_classes']).strip()
                            classes_list = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
                        if class_name not in classes_list:
                            logging.error(f"Teacher {contact_code} cannot access student class {class_name}")
                            return jsonify({"error": "Unauthorized access"}), 403
                        contact_name = bleach.clean(teacher['name'] or 'Unknown Teacher')
                    elif contact_type == 'parent':
                        query = "SELECT parent_name FROM parents WHERE id = %s"
                        cursor.execute(query, (contact_code,))
                        res = cursor.fetchone()
                        if res:
                            contact_name = bleach.clean(res['parent_name'] or 'Unknown Parent')
                        else:
                            logging.error(f"Parent {contact_code} not found")
                            return jsonify({"error": "Parent not found"}), 404
                    elif contact_type == 'headteacher':
                        ht = get_headteacher_data(conn)
                        if ht:
                            contact_name = bleach.clean(ht['name'] or 'Unknown Headteacher')
                        else:
                            logging.error("Headteacher not found")
                            return jsonify({"error": "Headteacher not found"}), 404

                messages = get_messages_for_user(conn, student_code, 'student', contact_code, contact_type)
                logging.info(f"Chat room loaded for student {student_code} with {contact_type}:{contact_code}, {len(messages)} messages")


                return render_template('chat_room.html',
                                    contact_name=contact_name or 'Unknown',
                                    contact_code=str(contact_code),
                                    contact_type=contact_type,
                                    messages=messages,
                                    current_user_id=student_code  ,
                                    current_user_type=user_type)



            elif user_type == 'teacher':
                teacher_code = session.get('teacher_code')
                if not teacher_code:
                    logging.error("Missing teacher_code in session")
                    return jsonify({"error": "Missing session data"}), 400

                if not is_valid_teacher_contact(teacher_code, contact_code, contact_type, conn):
                    logging.error(f"Unauthorized contact {contact_code} ({contact_type}) for teacher {teacher_code}")
                    flash("You are not authorized to access this chat", "error")
                    return redirect(url_for('chats'))

                with conn.cursor(dictionary=True) as cursor:
                    if contact_type == 'student':
                        query_teacher = "SELECT accessible_classes FROM teachers WHERE code = %s"
                        cursor.execute(query_teacher, (teacher_code,))
                        res = cursor.fetchone()
                        if not res:
                            logging.error(f"Teacher {teacher_code} not found")
                            return jsonify({"error": "Teacher not found"}), 404
                        try:
                            accessible_classes = json.loads(res['accessible_classes'])
                        except json.JSONDecodeError:
                            cleaned = re.sub(r'[\[\]\s\'"]', '', res['accessible_classes']).strip()
                            accessible_classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
                        
                        for class_name in accessible_classes:
                            student_data = get_student_data(conn, class_name, contact_code)
                            if not isinstance(student_data, tuple):
                                contact_name = bleach.clean(student_data.get('name', 'Unknown Student'))
                                break
                        if contact_name is None:
                            logging.error(f"Student {contact_code} not found in accessible classes for teacher {teacher_code}")
                            return jsonify({"error": "Student not found"}), 404
                    elif contact_type == 'parent':
                        query = "SELECT parent_name FROM parents WHERE student_code = %s"
                        cursor.execute(query, (contact_code,))
                        res = cursor.fetchone()
                        if res:
                            contact_name = bleach.clean(res['parent_name'] or 'Unknown Parent')
                        else:
                            logging.error(f"Parent {contact_code} not found")
                            return jsonify({"error": "Parent not found"}), 404
                    elif contact_type == 'teacher':
                        query = "SELECT name FROM teachers WHERE code = %s"
                        cursor.execute(query, (contact_code,))
                        res = cursor.fetchone()
                        if res:
                            contact_name = bleach.clean(res['name'] or 'Unknown Teacher')
                        else:
                            logging.error(f"Teacher {contact_code} not found")
                            return jsonify({"error": "Teacher not found"}), 404
                    elif contact_type == 'headteacher':
                        ht = get_headteacher_data(conn)
                        if ht:
                            contact_name = bleach.clean(ht['name'] or 'Unknown Headteacher')
                        else:
                            logging.error("Headteacher not found")
                            return jsonify({"error": "Headteacher not found"}), 404

                messages = get_messages_for_user(conn, teacher_code, 'teacher', contact_code, contact_type)
                logging.info(f"Chat room loaded for teacher {teacher_code} with {contact_type}:{contact_code}, {len(messages)} messages")

            
                return render_template('chat_room.html',
                                    contact_name=contact_name or 'Unknown',
                                    contact_code=str(contact_code),
                                    contact_type=contact_type,
                                    messages=messages,
                                    current_user_id=teacher_code  ,
                                    current_user_type=user_type)

           




            elif user_type == 'headteacher':
                headteacher_code = session.get('headteacher_code')
                if not headteacher_code:
                    logging.error("Missing headteacher_code in session")
                    flash("Missing session data", "error")
                    return redirect(url_for('login'))
                
                if not is_valid_headteacher_contact(headteacher_code, contact_code, contact_type, conn):
                    logging.error(f"Unauthorized contact {contact_code} ({contact_type}) for headteacher {headteacher_code}")
                    flash("You are not authorized to access this chat", "error")
                    return redirect(url_for('chats'))
                
                contact_name = None
                with conn.cursor(dictionary=True) as cursor:
                    if contact_type == 'teacher':
                        query = "SELECT name FROM teachers WHERE code = %s"
                        cursor.execute(query, (contact_code,))
                        result = cursor.fetchone()
                        contact_name = bleach.clean(result['name']) if result else 'Unknown Teacher'
                    else:
                        logging.error(f"Invalid contact type: {contact_type}")
                        flash("Invalid contact type", "error")
                        return redirect(url_for('chats'))
                
                messages = get_messages_for_user(conn, headteacher_code, 'headteacher', contact_code, contact_type)
                logging.info(f"Chat room loaded for headteacher {headteacher_code} with {contact_type}:{contact_code}")
                return render_template('chat_room.html', 
                                    contact_name=contact_name, 
                                    contact_code=contact_code, 
                                    contact_type=contact_type, 
                                    messages=messages,
                                    current_user_id=headteacher_code)





            elif user_type == 'parent':
                student_code = session.get('student_code')
                
                if not student_code:
                    logging.error("Missing student_code in session for parent")
                    return jsonify({"error": "Missing session data"}), 400
                
                try:
                    student_code_int = int(student_code)
                    contact_code_int = int(contact_code)
                except ValueError:
                    logging.error(f"Invalid code format: student_code={student_code}, contact_code={contact_code}")
                    return jsonify({"error": "Invalid code format"}), 400
                
                if not is_valid_parent_contact(student_code_int, contact_code_int, contact_type, conn):
                    logging.error(f"Unauthorized contact {contact_code} ({contact_type}) for parent of student {student_code}")
                    flash("You are not authorized to access this chat", "error")
                    return redirect(url_for('chats'))
                
                with conn.cursor(dictionary=True) as cursor:
                    if contact_type == 'teacher':
                        query = "SELECT name FROM teachers WHERE code = %s"
                        cursor.execute(query, (contact_code_int,))
                        result = cursor.fetchone()
                        contact_name = bleach.clean(result['name']) if result else 'Unknown Teacher'
                    else:
                        logging.error(f"Invalid contact type for parent: {contact_type}")
                        return jsonify({"error": "Invalid contact type"}), 400
                
                messages = get_messages_for_user(conn, student_code_int, 'parent', contact_code_int, contact_type)
                logging.info(f"Chat room loaded for parent of student {student_code} with {contact_type}:{contact_code}")
                
                return render_template('chat_room.html', 
                                    contact_name=contact_name, 
                                    contact_code=contact_code, 
                                    contact_type=contact_type, 
                                    messages=messages,
                                    current_user_id=student_code_int,
                                    current_user_type=user_type)

        except mysql.connector.Error as err:
            logging.error(f"Database error in chat_room: {str(err)}")
            flash("Database error occurred", "error")
            return redirect(url_for('login'))
        finally:
            if conn.is_connected():
                conn.close()





    @app.route('/send_message', methods=['POST'])
    @limiter.limit(LIMIT)
    def send_message_route():
        if 'user_type' not in session:
            logging.error("Unauthorized access to send_message: no user_type in session")
            return jsonify({"error": "Unauthorized access"}), 401
        
        user_type = session.get('user_type')
        school_stage = session.get('school_stage')
        
        if not school_stage:
            logging.error("Missing school_stage in session")
            return jsonify({"error": "Missing session data: school stage"}), 400
        
        conn = get_connection_by_stage(school_stage)
        if not conn:
            logging.error(f"Invalid school stage: {school_stage}")
            return jsonify({"error": "Invalid school stage"}), 400
        
        try:
            data = request.get_json()
            logging.debug(f"Received send_message payload: {data}")
            
            receiver_id = data.get('receiver_id')
            receiver_type = data.get('receiver_type')
            message = data.get('message')
            reply_to_message_id = data.get('reply_to_message_id')
            
            if not receiver_id or not receiver_type or not message:
                logging.error(f"Invalid payload: receiver_id={receiver_id}, receiver_type={receiver_type}, message={message}")
                return jsonify({"error": "Missing required fields: receiver_id, receiver_type, or message"}), 400
            
            if user_type == 'student':
                sender_id = session.get('student_code')
                if not sender_id:
                    logging.error("Missing student_code in session")
                    return jsonify({"error": "Missing session data"}), 400
                
                valid_types = ['student', 'teacher']
                if receiver_type not in valid_types:
                    logging.error(f"Invalid receiver type: {receiver_type}")
                    return jsonify({"error": "Invalid receiver type"}), 400
                
                try:
                    receiver_id = int(receiver_id)
                except (ValueError, TypeError):
                    logging.error(f"Invalid receiver_id: {receiver_id}")
                    return jsonify({"error": "Invalid receiver ID"}), 400
                
                if reply_to_message_id:
                    try:
                        reply_to_message_id = int(reply_to_message_id)
                    except (ValueError, TypeError):
                        logging.error(f"Invalid reply_to_message_id: {reply_to_message_id}")
                        return jsonify({"error": "Invalid reply to message ID"}), 400
                
                cleaned_message = bleach.clean(message)
                send_message(conn, sender_id, 'student', receiver_id, receiver_type, cleaned_message, reply_to_message_id)
                conn.commit()
                logging.debug(f"Message sent by student {sender_id} to {receiver_type}:{receiver_id}")
                return jsonify({"status": "Message sent successfully"}), 200
            
            elif user_type == 'teacher':
                sender_id = session.get('teacher_code')
                if not sender_id:
                    logging.error("Missing teacher_code in session")
                    return jsonify({"error": "Missing session data: teacher code"}), 400
                
                try:
                    sender_id = int(sender_id)
                    receiver_id = int(receiver_id)
                    if reply_to_message_id:
                        reply_to_message_id = int(reply_to_message_id)
                except (ValueError, TypeError) as e:
                    logging.error(f"Invalid ID format: sender_id={sender_id}, receiver_id={receiver_id}, reply_to_message_id={reply_to_message_id}, error={str(e)}")
                    return jsonify({"error": "Invalid sender or receiver ID format"}), 400
                
                valid_types = ['student', 'teacher', 'parent', 'headteacher']
                if receiver_type not in valid_types:
                    logging.error(f"Invalid receiver type: {receiver_type}")
                    return jsonify({"error": f"Invalid receiver type: {receiver_type} not in {valid_types}"}), 400
                
                if not is_valid_teacher_contact(sender_id, receiver_id, receiver_type, conn):
                    logging.error(f"Unauthorized send to {receiver_type}:{receiver_id} by teacher {sender_id}")
                    return jsonify({"error": "Unauthorized: You cannot send messages to this contact"}), 403
                
                cleaned_message = bleach.clean(message)
                success = send_message(conn, sender_id, 'teacher', receiver_id, receiver_type, cleaned_message, reply_to_message_id)
                if success:
                    conn.commit()
                    logging.info(f"Message sent by teacher {sender_id} to {receiver_type}:{receiver_id}")
                    return jsonify({"status": "Message sent successfully"}), 200
                else:
                    logging.error(f"Failed to send message by teacher {sender_id}")
                    return jsonify({"error": "Failed to send message due to database error"}), 500
            




            elif user_type == 'headteacher':
                sender_id = session.get('headteacher_code')
                if not sender_id:
                    logging.error("Missing headteacher_code in session")
                    return jsonify({"error": "Missing session data: headteacher code"}), 400
                
                try:
                    sender_id = int(sender_id)
                    receiver_id = int(receiver_id)
                    if reply_to_message_id:
                        reply_to_message_id = int(reply_to_message_id)
                except (ValueError, TypeError) as e:
                    logging.error(f"Invalid ID format: sender_id={sender_id}, receiver_id={receiver_id}, reply_to_message_id={reply_to_message_id}, error={str(e)}")
                    return jsonify({"error": "Invalid sender or receiver ID format"}), 400
                
                valid_types = ['teacher']
                if receiver_type not in valid_types:
                    logging.error(f"Invalid receiver type: {receiver_type}")
                    return jsonify({"error": f"Invalid receiver type: {receiver_type} not in {valid_types}"}), 400
                
                if not is_valid_headteacher_contact(sender_id, receiver_id, receiver_type, conn):
                    logging.error(f"Unauthorized send to {receiver_type}:{receiver_id} by headteacher {sender_id}")
                    return jsonify({"error": "Unauthorized: You cannot send messages to this contact"}), 403
                
                cleaned_message = bleach.clean(message)
                success = send_message(conn, sender_id, 'headteacher', receiver_id, receiver_type, cleaned_message, reply_to_message_id)
                if success:
                    conn.commit()
                    logging.info(f"Message sent by headteacher {sender_id} to {receiver_type}:{receiver_id}")
                    return jsonify({"status": "Message sent successfully"}), 200
                else:
                    logging.error(f"Failed to send message by headteacher {sender_id}")
                    return jsonify({"error": "Failed to send message due to database error"}), 500





            elif user_type == 'parent':
                student_code = session.get('student_code')
                if not student_code:
                    logging.error("Missing student_code in session for parent")
                    return jsonify({"error": "Missing session data"}), 400
                
                try:
                    student_code_int = int(student_code)
                    receiver_id_int = int(receiver_id)
                    if reply_to_message_id:
                        reply_to_message_id = int(reply_to_message_id)
                except (ValueError, TypeError) as e:
                    logging.error(f"Invalid ID format: student_code={student_code}, receiver_id={receiver_id}, error={str(e)}")
                    return jsonify({"error": "Invalid sender or receiver ID format"}), 400
                
                valid_types = ['teacher']
                if receiver_type not in valid_types:
                    logging.error(f"Invalid receiver type: {receiver_type}")
                    return jsonify({"error": f"Invalid receiver type: {receiver_type} not in {valid_types}"}), 400
                
                if not is_valid_parent_contact(student_code_int, receiver_id_int, receiver_type, conn):
                    logging.error(f"Unauthorized send to {receiver_type}:{receiver_id} by parent of student {student_code}")
                    return jsonify({"error": "Unauthorized: You cannot send messages to this contact"}), 403
                
                cleaned_message = bleach.clean(message)
                success = send_message(conn, student_code_int, 'parent', receiver_id_int, receiver_type, cleaned_message, reply_to_message_id)
                if success:
                    conn.commit()
                    logging.info(f"Message sent by parent of student {student_code} to {receiver_type}:{receiver_id}")
                    return jsonify({"status": "Message sent successfully"}), 200
                else:
                    logging.error(f"Failed to send message by parent of student {student_code}")
                    return jsonify({"error": "Failed to send message due to database error"}), 500
        except mysql.connector.Error as err:
            logging.error(f"Database error in send_message: {str(err)}")
            return jsonify({"error": f"Database error: {str(err)}"}), 500
        finally:
            if conn.is_connected():
                conn.close()
    

















    @app.route('/get_messages/<contact_code>/<contact_type>', methods=['GET'])
    @limiter.limit(LIMIT)
    def get_messages(contact_code, contact_type):
        if 'user_type' not in session:
            logging.error("Unauthorized access to get_messages: no user_type in session")
            return jsonify({"error": "Unauthorized access"}), 401
        
        user_type = session.get('user_type')
        school_stage = session.get('school_stage')
        
        if not school_stage:
            logging.error("Missing school_stage in session")
            return jsonify({"error": "Missing session data: school stage"}), 400
        
        conn = get_connection_by_stage(school_stage)
        if not conn:
            logging.error(f"Invalid school stage: {school_stage}")
            return jsonify({"error": "Invalid school stage"}), 400
        
        try:
            if user_type == 'student':
                if session['user_type'] != 'student':
                    logging.error("Unauthorized access to get_messages: user_type not student")
                    return jsonify({"error": "Unauthorized access"}), 401
                
                student_code = session.get('student_code')
                if not student_code:
                    logging.error("Missing student_code in session")
                    return jsonify({"error": "Missing session data"}), 400
                
                try:
                    contact_code = int(contact_code)
                except ValueError:
                    logging.error(f"Invalid contact_code: {contact_code}")
                    return jsonify({"error": "Invalid contact code"}), 400
                
                valid_types = ['student', 'teacher']
                if contact_type not in valid_types:
                    logging.error(f"Invalid contact_type: {contact_type}")
                    return jsonify({"error": "Invalid contact type"}), 400
                
                messages = get_messages_for_user(conn, student_code, 'student', contact_code, contact_type)
                cleaned_messages = []
                for msg in messages:
                    cleaned_msg = msg.copy()
                    cleaned_msg['message'] = bleach.clean(msg['message'])
                    cleaned_msg['created_at'] = msg['created_at'].isoformat()
                    cleaned_messages.append(cleaned_msg)
                
                return jsonify({"messages": cleaned_messages}), 200
            
            elif user_type == 'teacher':
                teacher_code = session.get('teacher_code')
                if not teacher_code:
                    logging.error("Missing teacher_code in session")
                    return jsonify({"error": "Missing session data: teacher code"}), 400
                
                try:
                    teacher_code = int(teacher_code)
                    contact_code = int(contact_code)
                except ValueError:
                    logging.error(f"Invalid ID format: teacher_code={teacher_code}, contact_code={contact_code}")
                    return jsonify({"error": "Invalid teacher or contact code format"}), 400
                
                valid_types = ['student', 'teacher', 'parent', 'headteacher']
                if contact_type not in valid_types:
                    logging.error(f"Invalid contact type: {contact_type}")
                    return jsonify({"error": f"Invalid contact type: {contact_type} not in {valid_types}"}), 400
                
                if not is_valid_teacher_contact(teacher_code, contact_code, contact_type, conn):
                    logging.error(f"Unauthorized access to messages for teacher {teacher_code} with {contact_type}:{contact_code}")
                    return jsonify({"error": "Unauthorized: You cannot view messages with this contact"}), 403
                
                messages = get_messages_for_user(conn, teacher_code, 'teacher', contact_code, contact_type)
                cleaned_messages = []
                for msg in messages:
                    cleaned_msg = msg.copy()
                    cleaned_msg['message'] = bleach.clean(msg['message'])
                    cleaned_msg['created_at'] = msg['created_at'].isoformat()
                    cleaned_messages.append(cleaned_msg)
                
                logging.info(f"Fetched {len(cleaned_messages)} messages for teacher:{teacher_code} with {contact_type}:{contact_code}")
                return jsonify({"messages": cleaned_messages}), 200
            




            elif user_type == 'teacher':
                teacher_code = session.get('teacher_code')
                if not teacher_code:
                    logging.error("Missing teacher_code in session")
                    return jsonify({"error": "Missing session data: teacher code"}), 400
                
                try:
                    teacher_code = int(teacher_code)
                    contact_code = int(contact_code)
                except ValueError:
                    logging.error(f"Invalid ID format: teacher_code={teacher_code}, contact_code={contact_code}")
                    return jsonify({"error": "Invalid teacher or contact code format"}), 400
                
                valid_types = ['student', 'teacher', 'parent', 'headteacher']
                if contact_type not in valid_types:
                    logging.error(f"Invalid contact type: {contact_type}")
                    return jsonify({"error": f"Invalid contact type: {contact_type} not in {valid_types}"}), 400
                
                if not is_valid_teacher_contact(teacher_code, contact_code, contact_type, conn):
                    logging.error(f"Unauthorized access to messages for teacher {teacher_code} with {contact_type}:{contact_code}")
                    return jsonify({"error": "Unauthorized: You cannot view messages with this contact"}), 403
                
                messages = get_messages_for_user(conn, teacher_code, 'teacher', contact_code, contact_type)
                cleaned_messages = []
                for msg in messages:
                    cleaned_msg = msg.copy()
                    cleaned_msg['message'] = bleach.clean(msg['message'])
                    cleaned_msg['created_at'] = msg['created_at'].isoformat()
                    cleaned_messages.append(cleaned_msg)
                
                logging.info(f"Fetched {len(cleaned_messages)} messages for teacher:{teacher_code} with {contact_type}:{contact_code}")
                return jsonify({"messages": cleaned_messages}), 200
            
            elif user_type == 'headteacher':
                sender_id = session.get('headteacher_code')
                if not sender_id:
                    logging.error("Missing headteacher_code in session")
                    return jsonify({"error": "Missing session data: headteacher code"}), 400
                
                try:
                    sender_id = int(sender_id)
                    contact_code = int(contact_code)
                except ValueError:
                    logging.error(f"Invalid ID format: sender_id={sender_id}, contact_code={contact_code}")
                    return jsonify({"error": "Invalid headteacher or contact code format"}), 400
                
                valid_types = ['teacher']
                if contact_type not in valid_types:
                    logging.error(f"Invalid contact type: {contact_type}")
                    return jsonify({"error": f"Invalid contact type: {contact_type} not in {valid_types}"}), 400
                
                if not is_valid_headteacher_contact(sender_id, contact_code, contact_type, conn):
                    logging.error(f"Unauthorized access to messages for headteacher {sender_id} with {contact_type}:{contact_code}")
                    return jsonify({"error": "Unauthorized: You cannot view messages with this contact"}), 403
                
                messages = get_messages_for_user(conn, sender_id, 'headteacher', contact_code, contact_type)
                cleaned_messages = []
                for msg in messages:
                    cleaned_messages.append({
                        'id': msg['id'],
                        'sender_id': msg['sender_id'],
                        'sender_type': msg['sender_type'],
                        'receiver_id': msg['receiver_id'],
                        'receiver_type': msg['receiver_type'],
                        'message': bleach.clean(msg['message']),
                        'is_read': msg['is_read'],
                        'reply_to_message_id': msg['reply_to_message_id'],
                        'created_at': msg['created_at'].isoformat()
                    })
                logging.info(f"Fetched {len(cleaned_messages)} messages for headteacher:{sender_id} with {contact_type}:{contact_code}")
                return jsonify({"messages": cleaned_messages}), 200





            elif user_type == 'parent':
                student_code = session.get('student_code')
                if not student_code:
                    logging.error("Missing student_code in session for parent")
                    return jsonify({"error": "Missing session data"}), 400
                
                try:
                    student_code_int = int(student_code)
                    contact_code_int = int(contact_code)
                except ValueError:
                    logging.error(f"Invalid ID format: student_code={student_code}, contact_code={contact_code}")
                    return jsonify({"error": "Invalid student or contact code format"}), 400
                
                valid_types = ['teacher']
                if contact_type not in valid_types:
                    logging.error(f"Invalid contact type: {contact_type}")
                    return jsonify({"error": f"Invalid contact type: {contact_type} not in {valid_types}"}), 400
                
                if not is_valid_parent_contact(student_code_int, contact_code_int, contact_type, conn):
                    logging.error(f"Unauthorized access to messages for parent of student {student_code} with {contact_type}:{contact_code}")
                    return jsonify({"error": "Unauthorized: You cannot view messages with this contact"}), 403
                
                messages = get_messages_for_user(conn, student_code_int, 'parent', contact_code_int, contact_type)
                cleaned_messages = []
                for msg in messages:
                    cleaned_msg = msg.copy()
                    cleaned_msg['message'] = bleach.clean(msg['message'])
                    cleaned_msg['created_at'] = msg['created_at'].isoformat()
                    cleaned_messages.append(cleaned_msg)
                
                logging.info(f"Fetched {len(cleaned_messages)} messages for parent of student:{student_code} with {contact_type}:{contact_code}")
                return jsonify({"messages": cleaned_messages}), 200

        except mysql.connector.Error as err:
            logging.error(f"Database error in get_messages: {str(err)}")
            return jsonify({"error": f"Database error: {str(err)}"}), 500
        finally:
            if conn.is_connected():
                conn.close()




###################################################






    @app.route('/education_admin', methods=['GET', 'POST'])
    @limiter.limit(LIMIT)
    def education_admin_login():
        form = EducationAdminLoginForm()
        if form.validate_on_submit():
            school_stage = form.school_stage.data
            admin_code = form.admin_code.data
            admin_password = form.admin_password.data

            # تحديد قاعدة البيانات بناءً على school_stage
            conn = get_connection_by_stage(school_stage)
            if not conn:
                return render_template('education_admin.html', form=form, error=bleach.clean('Invalid school stage'))

            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM admin WHERE code = %s AND pass = %s"
                cursor.execute(query, (admin_code, admin_password))
                admin = cursor.fetchone()

                if admin:
                    session['user_type'] = 'education_admin'
                    session['admin_code'] = str(admin_code)
                    session['school_stage'] = school_stage
                    return redirect(url_for('education_admin_dashboard'))
                else:
                    return render_template('education_admin.html', form=form, error=bleach.clean('Invalid admin code or password'))
            except mysql.connector.Error as err:
                logging.error(f"Database error in education_admin_login: {err}")
                return render_template('education_admin.html', form=form, error=bleach.clean('Database error occurred'))
            finally:
                if conn.is_connected():
                    conn.close()
        return render_template('education_admin.html', form=form)








    @app.route('/education_admin_dashboard', methods=['GET', 'POST'])
    def education_admin_dashboard():
        if session.get('user_type') != 'education_admin':
            return redirect(url_for('index'))
        
        school_stage = session.get('school_stage')
        conn = get_connection_by_stage(school_stage)
        if not conn:
            return redirect(url_for('index'))
        
        classes = get_all_classes(conn)
        grades = sorted(set(int(cls.split('_')[0].replace('class', '')) for cls in classes))
        
        error = None
        attendance_data = None
        stats = {}
        current_date = datetime.today().strftime('%Y-%m-%d')
        
        if request.method == 'POST':
            scope = request.form.get('scope')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if start_date > end_date:
                    raise ValueError("Start date cannot be after end date")
            except ValueError as e:
                error = str(e)
                flash(error, 'error')
            else:
                selected_classes = []
                if scope == 'school':
                    selected_classes = classes
                elif scope == 'grade':
                    grade = request.form.get('grade')
                    selected_classes = get_classes_for_grade(classes, grade)
                elif scope == 'class':
                    class_name = request.form.get('class_name')
                    selected_classes = [class_name]
                
                if selected_classes:
                    attendance_data = get_attendance_data(conn, selected_classes, start_date, end_date)
                    stats = calculate_statistics(attendance_data)
                else:
                    error = "No classes found for selection"
        
        conn.close()
        
        return render_template('admin_dashboard.html',
                            school_stage=school_stage,
                            grades=grades,
                            classes=classes,
                            error=error,
                            attendance_data=attendance_data,
                            **stats,
                            current_date=current_date)








    @app.route('/chatbot', methods=['GET'])
    def chatbot():
        pass






    return app




if __name__ == "__main__":
    cncter = mysql.connector.connect(host="localhost", user="root", password="")
    print ("Preparing and setting up the database")
    print ("If database already prepared enter 1")
    print ("If you want to set up database enter 0")
    num_1 = 1#int(input("Enter : "))
    database_name = ""
    if num_1 == 0 :
        print ("Enter school type  [High school : 1 , Middle school : 2 ,Elementary school : 3 ]: ")
        num_2 = int(input(":"))
        if num_2 == 1 :
            create_school_database("high",cncter)
            database_name = "schooldata"
        elif num_2 == 2 :
            create_school_database("middle",cncter)
            database_name = "schooldata2"
        elif num_2 == 3 :
            create_school_database("elementary",cncter)
            database_name = "schooldata3"
        
        name = input("Enter headteacher name")
        code = int(input ("Enter headteacher code"))
        password = input ("Enter headteacher pasword")
        manager(cncter,code,password,name)
        print ("Now Go to this link ")
        print ("http://127.0.0.1:5000")



    app = server_1("schooldata3",'schooldata2','schooldata')
    app.run(host="0.0.0.0", port=5000, debug=True)
