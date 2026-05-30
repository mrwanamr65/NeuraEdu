import mysql.connector
from datetime import datetime
import logging
import os
import bleach
import re
from flask import jsonify,json,render_template,session,redirect,url_for
from typing import Optional

logging.basicConfig(filename=os.path.join('logs', 'errors.log'), level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')



def connection(database):
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=database
    )





def process_attendance_data(student):
    schedule = []
    for key, value in student.items():
        if len(key) == 9 and key.isdigit():
            year = key[:4]
            month = key[4:6]
            day = key[6:8]
            session = key[8]
            status = "Present" if value == "True" else "Absent"
            schedule.append({
                "date": f"{year}-{month}-{day}",
                "session": session,
                "status": status
            })
    schedule.sort(key=lambda x: (x["date"], x["session"]))
    return schedule



def get_student_data(connection, class_, code):
    cursor = connection.cursor()
    try:
        query = f"SELECT * FROM {class_} WHERE code = %s"
        cursor.execute(query, (code,))
        column_names = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        if row:
            row_data = dict(zip(column_names, row))
            return row_data
        return {"error": f"Student {code} does not exist"}, 404
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {"error": str(err)}, 500
    finally:
        cursor.close()










def get_classes(connection, code, stage_, url_):
    cursor = connection.cursor(dictionary=True)
    try:
        # التحقق من أن code رقمي
        try:
            code_int = int(code)
        except ValueError:
            return jsonify({"error": "Invalid teacher code format"}), 400

        query = "SELECT accessible_classes FROM teachers WHERE code = %s"
        cursor.execute(query, (code_int,))
        res = cursor.fetchone()
        if not res:
            return jsonify({"error": "Teacher not found"}), 404

        # تحليل accessible_classes بأمان
        classes_list_ = []
        if res['accessible_classes']:
            raw_classes = res['accessible_classes']
            # إزالة الأقواس، المسافات البيضاء، وعلامات الاقتباس
            cleaned_classes = re.sub(r'[\[\]\s\'"]', '', raw_classes).strip()
            if cleaned_classes:
                # محاولة تحليل JSON أولاً
                try:
                    classes_list_ = json.loads(res['accessible_classes'])
                    # التأكد من أن كل عنصر هو سلسلة نصية
                    classes_list_ = [str(cls).strip() for cls in classes_list_ if isinstance(cls, str)]
                except json.JSONDecodeError:
                    # إذا فشل JSON، استخدام split مع تنظيف إضافي
                    classes_list_ = [cls.strip() for cls in cleaned_classes.split(',') if cls.strip()]

        # تنظيف أسماء الفصول
        classes_list_clean = [bleach.clean(cls) for cls in classes_list_ if cls]
        if not classes_list_clean:
            return jsonify({"error": "No valid classes found"}), 404

        # تنظيف البيانات الأخرى
        stage_clean = bleach.clean(stage_)
        code_clean = bleach.clean(str(code))

        return render_template('teacher_choose_class.html', 
                            classes_list=classes_list_clean, 
                            school=stage_clean, 
                            url=url_, 
                            teacher_code=code_clean)
    except mysql.connector.errors.ProgrammingError as e:
        logging.error(f"Database error in get_classes: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_classes: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        if cursor:
            cursor.close()





def teacher_data(connect, code_, password, stage):
    cursor = connect.cursor(dictionary=True)
    try:
        try:
            code_int = int(code_)
        except ValueError:
            return jsonify({"error": "Invalid teacher code format"}), 400

        query = "SELECT password FROM teachers WHERE code = %s"
        cursor.execute(query, (code_int,))
        res = cursor.fetchone()

        if res and res["password"] == password:
            session['user_type'] = 'teacher' 
            session['teacher_code'] = str(code_int)
            session['school_stage'] = stage
            return redirect(url_for('teacher_dashboard'))
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except mysql.connector.errors.ProgrammingError as e:
        logging.error(f"Database error in teacher_data: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in teacher_data: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        if cursor:
            cursor.close()
        if connect.is_connected():
            connect.close()



def headteacher_data(connect, code_, password, stage):
    cursor = connect.cursor(dictionary=True)
    try:
        try:
            code_int = int(code_)
        except ValueError:
            return jsonify({"error": "Invalid headteacher code format"}), 400

        query = "SELECT password FROM manager WHERE code = %s"
        cursor.execute(query, (code_int,))
        res = cursor.fetchone()

        if res and res["password"] == password:
            # نحفظ الحالة في الجلسة ونحوّل لصفحة الداشبورد
            session['user_type'] = 'headteacher'
            session['headteacher_code'] = str(code_int)
            session['school_stage'] = stage
            return redirect(url_for('headteacher_dashboard_page'))
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except mysql.connector.errors.ProgrammingError as e:
        logging.error(f"Database error in headteacher_data: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in headteacher_data: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        if cursor:
            cursor.close()
        if connect.is_connected():
            connect.close()



def my_students(class_name, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        query = f"SELECT code, name FROM {class_name}"
        cursor.execute(query)
        students_dict = {str(row['code']): row['name'] for row in cursor.fetchall()}
        print("Students data fetched successfully!")
        return students_dict
    except mysql.connector.Error as err:
        print(f"Error fetching students data: {err}")
        return {}
    finally:
        cursor.close()



def fetch_all_notifications(cncter_1, class_name):
    cursor = cncter_1.cursor()
    try:
        select_query = f"""
        SELECT id, title, notification, notes FROM {class_name}_notifications
        """
        cursor.execute(select_query)
        results = cursor.fetchall()
        notifications_list = [{"id": row[0], "title": row[1], "notification": row[2], "notes": row[3]} for row in results]
        print("All notifications fetched successfully!")
        return notifications_list
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()



def add_student_evaluation(connection, class_name, student_code, evaluation, note):
    cursor = connection.cursor()
    try:
        date_today = datetime.now().strftime('%Y-%m-%d')
        insert_query = f"""
        INSERT INTO {class_name}_evaluations (student_code, date, evaluation, note)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (student_code, date_today, evaluation, note))
        connection.commit()
        print(f"Evaluation added successfully for student {student_code}!")
        return True
    except mysql.connector.Error as err:
        print(f"Error adding evaluation: {err}")
        return False
    finally:
        cursor.close()



def get_student_evaluations(connection, class_name, student_code):
    cursor = connection.cursor(dictionary=True)
    try:
        # تنظيف الإدخال
        class_name_clean = bleach.clean(class_name)
        student_code_clean = bleach.clean(str(student_code))  # تحويل student_code إلى نص للتوافق

        if not class_name_clean or not student_code_clean:
            logging.error("Invalid class_name or student_code provided to get_student_evaluations")
            return []

        # التحقق من أن class_name يحتوي على أحرف صالحة (يسمح بـ a-z, A-Z, 0-9, _)
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            logging.error(f"Invalid class_name format: {class_name_clean}")
            return []

        select_query = """
        SELECT date, evaluation, note, id 
        FROM {}_evaluations 
        WHERE student_code = %s 
        ORDER BY date DESC
        """.format(class_name_clean)  # ملاحظة: يُفضل استخدام قائمة فصول مسموح بها للأمان

        cursor.execute(select_query, (student_code_clean,))
        evaluations = cursor.fetchall()

        # تنظيف البيانات المُرجعة
        cleaned_evaluations = []
        for eval in evaluations:
            cleaned_eval = {
                'date': bleach.clean(str(eval['date'])),
                'evaluation': bleach.clean(eval['evaluation']),
                'note': bleach.clean(eval['note'] if eval['note'] else ''),
                'id': eval['id']  # id عادةً لا يحتاج تنظيف لأنه رقم
            }
            cleaned_evaluations.append(cleaned_eval)

        logging.info(f"Evaluations fetched successfully for student {student_code_clean} in class {class_name_clean}")
        return cleaned_evaluations
    except mysql.connector.errors.ProgrammingError as err:
        logging.error(f"Database error in get_student_evaluations: {str(err)}")
        return []
    except Exception as err:
        logging.error(f"Unexpected error in get_student_evaluations: {str(err)}")
        return []
    finally:
        if cursor:
            cursor.close()








def create_school_database(school_type, cncter):
    db_map = {"high": "schooldata", "middle": "schooldata2", "elementary": "schooldata3"}
    database_name = db_map.get(school_type.lower(), "schooldata")  
    try:
        cursor = cncter.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        cncter.database = database_name
        print(f"{database_name} created or already exists.")
        print(f"Successful connection with {database_name}")
        return database_name
    except mysql.connector.Error as e:
        logging.error(f"Error creating database {database_name}: {e}")
        print(f"Error creating database {database_name}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error creating database {database_name}: {e}")
        print(f"Unexpected error: {e}")
        return None
    finally:
        create_teachers_table(cncter)
        create_subjects_table(cncter)
        create_parents_table(cncter) 
        create_parents_notifications_table(cncter)

        if 'cncter' in locals() and cncter.is_connected():
            cursor.close()
            





def create_teachers_table(cncter):
    try:
        cursor = cncter.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                code INT PRIMARY KEY,
                name TEXT,
                accessible_classes TEXT,
                password TEXT
            )
        """)
        cncter.commit()
        print("Teachers table created or already exists.")
    except Exception as e:
        logging.error(f"Error creating teachers table: {e}")
        print(f"Error: {e}")
    finally:
        if cncter.is_connected():
            cursor.close()






def create_subjects_table(cncter):
    try:
        cursor = cncter.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE
            )
        """)
        cncter.commit()
        print("Subjects table created or already exists.")
        return True
    except mysql.connector.Error as e:
        logging.error(f"Error creating subjects table: {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()






def create_parents_table(cncter):
    try:
        cursor = cncter.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_code INT NOT NULL,
                parent_name VARCHAR(255) NOT NULL,
                parent_password VARCHAR(255) NOT NULL,
                phone_number VARCHAR(20),  
                UNIQUE KEY unique_student (student_code)
            )
        """)
        cncter.commit()
        print("Parents table created or already exists.")
    except Exception as e:
        logging.error(f"Error creating parents table : {e}")
        print(f"Error: {e}")
    finally:
        if cncter.is_connected():
            cursor.close()






def create_parents_notifications_table(cncter):
    try:
        cursor = cncter.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parents_notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT,
                notification TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cncter.commit()
        print("Parents notifications table created or already exists.")
    except Exception as e:
        logging.error(f"Error creating parents notifications table : {e}")
        print(f"Error: {e}")
    finally:
        if cncter.is_connected():
            cursor.close()






def create_class(conn, class_name):
    success = False
    try:
        cursor = conn.cursor()
        if conn.is_connected():
            print(f"Connected")        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {class_name} (
                code INT PRIMARY KEY,
                name TEXT,
                age INT,
                class TEXT,
                last_time_seen TEXT,
                password TEXT
            )
        """)
        create_class_videos (conn, class_name)
        conn.commit()
        print(f"Class {class_name} created or already exists.")
        success = True  
        
    except Exception as e:
        logging.error(f"Error creating class {class_name}: {e}")
        print(f"Error: {e}")
        success = False
    finally:
        create_class_notifications(conn, class_name)
        create_evaluations_table(class_name, conn)
        if conn.is_connected():
            cursor.close()
        return success
        





def create_class_notifications(cncter, class_name):
    try:
        cursor = cncter.cursor()
        if cncter.is_connected():
            print(f"Connected")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {class_name}_notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT,
                notification TEXT,
                notes TEXT
            )
        """)
        cncter.commit()
        print(f"Table {class_name}_notifications created or already exists!")

    except Exception as e:
        if "MySQL server has gone away" in str(e) and cursor.rowcount >= 0:
            print("Ignoring MySQL server has gone away error as notifications table was created.")
        else:
            logging.error(f"Error creating notifications table {class_name}: {e}")
            print(f"Error: {e}")






def create_evaluations_table(class_name, cnct):
    try:
        cursor = cnct.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {class_name}_evaluations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_code INT,
                date DATE,
                evaluation VARCHAR(500),
                note TEXT
            )
        """)
        cnct.commit()
        print(f"Table {class_name}_evaluations created successfully!")
        
    except mysql.connector.Error as e:
        if "MySQL server has gone away" in str(e) and cursor.rowcount >= 0:
            print("Ignoring MySQL server has gone away error as evaluations table was created.")
        else:
            logging.error(f"Error creating evaluations table {class_name}: {e}")
            print(f"Error: {e}")






def create_class_videos (cncter, class_name):
    try:
        cursor = cncter.cursor()
        if cncter.is_connected():
            print(f"Connected with {cncter.database}")          
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {class_name}_videos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                link TEXT,
                subject TEXT,
                title TEXT)""")
        cncter.commit()
        print(f"Table {class_name}_videos created successfully!")
    except mysql.connector.Error as e:
        print(f"Error: {e}")






def add_student(cncter, student_code, student_name, student_age, class_name, password):
    try:
        cursor = cncter.cursor()
        cursor.execute(f"SELECT * FROM {class_name} WHERE code = %s", (student_code,))
        if cursor.fetchone():
            print("Error: Student with this code already exists.")
            return False
        
        cursor.execute(f"""
            INSERT INTO {class_name} (code, name, age, class, last_time_seen, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (student_code, student_name, student_age, class_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), password))
        
        cursor.execute(f"""
            INSERT INTO {class_name}_evaluations (student_code, date, evaluation, note)
            VALUES (%s, %s, %s, %s)
        """, (student_code, datetime.now().strftime("%Y-%m-%d"), "Registered", "Student added to class"))
        
        cncter.commit()
        print(f"Student {student_name} added successfully!")
        return True
        
    except Exception as e:
        logging.error(f"Error adding student {student_name}: {e}")
        print(f"Error: {e}")
        if cncter.is_connected():
            cncter.rollback()
        return False






def add_teacher(cncter, teacher_name, accessible_classes, teacher_password, teacher_code):
    try:
        cursor = cncter.cursor()

        
        cursor.execute("SELECT * FROM teachers WHERE code = %s", (teacher_code,))
        if cursor.fetchone():
            print("Error: Teacher with this code already exists.")
            return False
        
        cursor.execute("""
            INSERT INTO teachers (code, name, accessible_classes, password)
            VALUES (%s, %s, %s, %s)
        """, (teacher_code, teacher_name, str(accessible_classes), teacher_password))
        cncter.commit()
        print(f"Teacher {teacher_name} added successfully!")
        return True
    except Exception as e:
        logging.error(f"Error adding teacher {teacher_name}: {e}")
        print(f"Error: {e}")
        if cncter.is_connected():
            cncter.rollback()
        return False






def get_teachers2(cncter):
    try:
        cursor = cncter.cursor(dictionary=True)
        cursor.execute("SELECT code, name, accessible_classes FROM teachers")
        teachers_raw = cursor.fetchall()
        
        teachers = []
        for teacher in teachers_raw:
            try:
                accessible_classes_list = eval(teacher['accessible_classes']) if teacher['accessible_classes'] else []
                if not isinstance(accessible_classes_list, list):
                    accessible_classes_list = []
            except (SyntaxError, NameError) as e:
                logging.error(f"Error parsing accessible_classes for teacher {teacher['code']}: {e}")
                accessible_classes_list = []
            
            accessible_classes_str = ", ".join(accessible_classes_list) if accessible_classes_list else "No classes"
            
            teachers.append({
                'code': teacher['code'],
                'name': teacher['name'],
                'accessible_classes': accessible_classes_list,  
                'accessible_classes_str': accessible_classes_str  
            })
        
        print(f"Retrieved {len(teachers)} teachers from database '{cncter.database}'")
        return teachers
    except mysql.connector.Error as e:
        logging.error(f"Error retrieving teachers from {cncter}: {e}")
        print(f"Error: {e}")
        return []






def add_subject_with_teacher_table(cncter, subject_name):

    try:
        cursor = cncter.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{subject_name}` (
                teacher_code INT PRIMARY KEY
            )
        """)
        
        print(f"Table for subject '{subject_name}' created successfully!")
        add_subject(cncter, subject_name)  
        print(f"Subject '{subject_name}' added to subjects table.")
        cncter.commit()
        return True
    except mysql.connector.Error as e:
        logging.error(f"Error creating subject table '{subject_name}': {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()






def add_teacher_to_subject(cncter, subject_name, teacher_code):
    try:
        cursor = cncter.cursor()
        cursor.execute(f"INSERT INTO `{subject_name}` (teacher_code) VALUES (%s)", (teacher_code,))
        cncter.commit()
        print(f"Teacher {teacher_code} added to subject '{subject_name}' successfully!")
        return True
    except mysql.connector.Error as e:
        logging.error(f"Error adding teacher {teacher_code} to subject '{subject_name}': {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()






def add_subject(cncter, subject_name):
    try:
        cursor = cncter.cursor()
        cursor.execute("INSERT INTO subjects (name) VALUES (%s)", (subject_name,))
        cncter.commit()
        print(f"Subject '{subject_name}' added successfully!")
        return True
    except mysql.connector.Error as e:
        logging.error(f"Error adding subject '{subject_name}': {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()






def delete_subject(cncter, subject_name):
    try:
        cursor = cncter.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS `{subject_name}`")
        cursor.execute("DELETE FROM subjects WHERE name = %s", (subject_name,))
        cncter.commit()
        print(f"Subject '{subject_name}' and its table deleted successfully (if existed)!")
        return True
    except mysql.connector.Error as e:
        logging.error(f"Error deleting subject '{subject_name}': {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()





def add_parent_notification(cncter, title, notification, note):
    try:
        cursor = cncter.cursor()
        cursor.execute("""
            INSERT INTO parents_notifications (title, notification, notes)
            VALUES (%s, %s, %s)
        """, (title, notification, note))
        cncter.commit()
        print("Parent notification added successfully!")
        return True
    except Exception as e:
        logging.error(f"Error adding parent notification: {e}")
        print(f"Error: {e}")
        if cncter.is_connected():
            cncter.rollback()
        return False
    finally:
        if cncter.is_connected():
            cursor.close()
            





def fetch_all_parents_notifications(cncter):
    cursor = cncter.cursor()
    try:
        select_query = """
        SELECT id, title, notification, notes, created_at FROM parents_notifications
        ORDER BY created_at DESC
        """
        cursor.execute(select_query)
        results = cursor.fetchall()
        notifications_list = [{"id": row[0], "title": row[1], "notification": row[2], "notes": row[3], "created_at": row[4]} for row in results]
        print("All parents notifications fetched successfully!")
        return notifications_list
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()






def delete_parent_notification(cncter, notification_id):
    try:
        cursor = cncter.cursor()
        delete_query = "DELETE FROM parents_notifications WHERE id = %s"
        cursor.execute(delete_query, (notification_id,))
        cncter.commit()
        if cursor.rowcount > 0:
            print(f"Parent notification with ID {notification_id} deleted successfully.")
            return True
        else:
            print(f"No parent notification found with ID {notification_id}.")
            return False
    except Exception as e:
        logging.error(f"Error deleting parent notification: {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()
            





def manager (connection,manager_code,manager_password,manager_name):
    try:

        if connection.is_connected():
            cursor = connection.cursor()
            print("Connected to MySQL database")
            create_table_query = """
            CREATE TABLE IF NOT EXISTS manager (
            code INT ,
            name TEXT,
            password TEXT
            )
            """
            cursor.execute(create_table_query)
            connection.commit()
            insert_query = """
            INSERT INTO manager (code, name,password)
            VALUES (%s, %s, %s)
            """
            record = (manager_code,manager_name,manager_password)
            cursor.execute(insert_query, record)
            connection.commit()
            print(f"Record inserted successfully: {record}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # إغلاق الاتصال
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")





 
def add_video(cncter, class_name, link, subject,title):
    try:
        cursor = cncter.cursor()
        if cncter.is_connected():
            print(f"Connected with {cncter.database}")
        cursor.execute(f"""
            INSERT INTO {class_name}_videos (link, subject,title)
            VALUES (%s, %s, %s)
        """, (link,subject, title))
        cncter.commit()
        print("Video added successfully!")
        return True
    except mysql.connector.Error as e:
        logging.error(f"Error adding video to {class_name}: {e}")
        print(f"Error: {e}")






def delete_video(cncter, class_name, video_id):
    try:
        cursor = cncter.cursor()   
        if cncter.is_connected():
            print(f"Connected with {cncter.database}")
        cursor.execute(f"""
            DELETE FROM {class_name}_videos WHERE id = %s
        """, (video_id,))
        cncter.commit() 
        if cursor.rowcount > 0:
            print(f"Video with ID {video_id} deleted successfully from {class_name}_videos.")
            return True     
        else:
            print(f"No video found with ID {video_id} in {class_name}_videos.")
            return False
    except mysql.connector.Error as e:
        logging.error(f"Error deleting video from {class_name}: {e}")
        print(f"Error: {e}")
        return False
    finally:
        if cncter.is_connected():
            cursor.close()
            print("Cursor closed after deleting video.")
        else:
            print("Connection is not open, cursor not closed.") 






def add_parent(cncter, student_code, parent_name, parent_password, phone_number=None):  
    try:
        cursor = cncter.cursor()
        cursor.execute("""
            INSERT INTO parents (student_code, parent_name, parent_password, phone_number)  
            VALUES (%s, %s, %s, %s)
        """, (student_code, parent_name, parent_password, phone_number))  
        cncter.commit()
        print(f"Parent {parent_name} for student {student_code} added successfully!")
        return True
    except mysql.connector.Error as e:
        if e.errno == 1062: 
            print(f"Error: Parent for student code {student_code} already exists.")
        else:
            logging.error(f"Error adding parent {parent_name}: {e}")
            print(f"Error: {e}")
        if cncter.is_connected():
            cncter.rollback()
        return False
    except Exception as e:
        logging.error(f"Unexpected error adding parent {parent_name}: {e}")
        print(f"Unexpected error: {e}")
        if cncter.is_connected():
            cncter.rollback()
        return False
    finally:
        if cncter.is_connected():
            cursor.close()






def get_parent_data(connect, student_code, parent_password):
    cursor = connect.cursor(dictionary=True)
    try:
        query_parent = "SELECT parent_name FROM parents WHERE student_code = %s AND parent_password = %s"
        cursor.execute(query_parent, (student_code, parent_password))
        parent_res = cursor.fetchone()
        if not parent_res:
            return {"error": "Invalid parent credentials"}, 401

        cursor.execute("SHOW TABLES LIKE 'class%'")
        raw_rows = cursor.fetchall()
        all_tables = []
        for row in raw_rows:
            table_name = next(iter(row.values()))
            all_tables.append(table_name)
        
        class_tables = [table for table in all_tables if not table.endswith(('_evaluations', '_notifications', '_videos'))]

        student_data = None
        student_class = None
        for table_name in class_tables:
            try:
                query_student = f"SELECT * FROM {table_name} WHERE code = %s"
                cursor.execute(query_student, (student_code,))
                student_res = cursor.fetchone()
                if student_res:
                    student_data = student_res
                    student_class = table_name
                    break
            except mysql.connector.Error as e:
                continue 

        if not student_data:
            return {"error": "Student data not found"}, 404
        return {
            "parent_name": parent_res['parent_name'],
            "student_data": student_data,
            "student_class": student_class
        }

    except mysql.connector.Error as err:
        return {"error": str(err)}, 500
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        if cursor:
            cursor.close()





def delete_evaluation(conn, class_name, evaluation_id):

    cursor = conn.cursor()
    try:
        # تنظيف الإدخال
        class_name_clean = bleach.clean(class_name) if class_name else None
        evaluation_id_clean = bleach.clean(str(evaluation_id)) if evaluation_id else None

        # التحقق من وجود المعلمات
        if not class_name_clean or not evaluation_id_clean:
            logging.error(f"Missing required parameters: class_name={class_name_clean}, evaluation_id={evaluation_id_clean}")
            return False

        # التحقق من أن evaluation_id رقم صالح
        if not evaluation_id_clean.isdigit():
            logging.error(f"Invalid evaluation_id format: {evaluation_id_clean}")
            return False

        # التحقق من أن class_name يحتوي على أحرف صالحة
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            logging.error(f"Invalid class_name format: {class_name_clean}")
            return False

        # استعلام الحذف
        delete_query = """
        DELETE FROM {}_evaluations 
        WHERE id = %s
        """.format(class_name_clean)

        cursor.execute(delete_query, (evaluation_id_clean,))
        conn.commit()

        # التحقق من نجاح الحذف
        if cursor.rowcount > 0:
            logging.info(f"Evaluation {evaluation_id_clean} deleted successfully from {class_name_clean}_evaluations")
            return True
        else:
            logging.error(f"Evaluation {evaluation_id_clean} not found in {class_name_clean}_evaluations")
            return False

    except mysql.connector.errors.ProgrammingError as e:
        logging.error(f"Database error in delete_evaluation: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in delete_evaluation: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()





def fetch_all_notifications(conn, class_name):
   
    cursor = conn.cursor(dictionary=True)
    try:
        # تنظيف الإدخال
        class_name_clean = bleach.clean(class_name) if class_name else None

        # التحقق من وجود class_name
        if not class_name_clean:
            logging.error("Missing class_name in fetch_all_notifications")
            return []

        # التحقق من أن class_name يحتوي على أحرف صالحة
        if not re.match(r'^[a-zA-Z0-9_]+$', class_name_clean):
            logging.error(f"Invalid class_name format: {class_name_clean}")
            return []

        select_query = """
        SELECT id, title, notification, notes 
        FROM {}_notifications
        """.format(class_name_clean)
        cursor.execute(select_query)
        notifications_list = cursor.fetchall()
        logging.info(f"Fetched {len(notifications_list)} notifications for class {class_name_clean}")
        return notifications_list
    except mysql.connector.errors.ProgrammingError as e:
        logging.error(f"Database error in fetch_all_notifications: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in fetch_all_notifications: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()










def create_messages_table(connection):
    """
    Create the messages table in the specified database with support for reply_to_message_id.
    
    Args:
        connection: MySQL connection object.
    
    Returns:
        bool: True if table created successfully, False otherwise.
    """
    cursor = None
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            print("Connected to MySQL database")
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS messages (
                id INT NOT NULL AUTO_INCREMENT,
                sender_id INT NOT NULL,
                sender_type VARCHAR(20) NOT NULL,
                receiver_id INT NOT NULL,
                receiver_type VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                reply_to_message_id INT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                INDEX idx_sender (sender_id, sender_type),
                INDEX idx_receiver (receiver_id, receiver_type),
                FOREIGN KEY (reply_to_message_id) REFERENCES messages(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_query)
            connection.commit()
            print("Messages table created successfully")
            return True
            
    except mysql.connector.Error as err:
        logging.error(f"Database error in create_messages_table: {str(err)}")
        print(f"Error: {err}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in create_messages_table: {str(e)}")
        print(f"Unexpected error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()
            print("MySQL connection closed")





def get_messages_for_user(connection, user_id, user_type, other_id, other_type):
    """
    Retrieve all messages between the current user and the other user, sorted by creation date.
    
    Args:
        connection: MySQL connection object.
        user_id: ID of the current user (e.g., student_code).
        user_type: Type of the current user (e.g., 'student').
        other_id: ID of the other user.
        other_type: Type of the other user.
    
    Returns:
        list: List of messages as dictionaries, sorted by created_at ASC.
    """
    cursor = None
    messages = []
    try:
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT id, sender_id, sender_type, receiver_id, receiver_type, message, is_read, reply_to_message_id, created_at
            FROM messages
            WHERE 
                (sender_id = %s AND sender_type = %s AND receiver_id = %s AND receiver_type = %s)
                OR 
                (sender_id = %s AND sender_type = %s AND receiver_id = %s AND receiver_type = %s)
            ORDER BY created_at ASC
            """
            params = (user_id, user_type, other_id, other_type, other_id, other_type, user_id, user_type)
            cursor.execute(query, params)
            messages = cursor.fetchall()
            
            print(f"Fetched {len(messages)} messages between {user_type}:{user_id} and {other_type}:{other_id}")
            return messages
            
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_messages_for_user: {str(err)}")
        print(f"Error: {err}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in get_messages_for_user: {str(e)}")
        print(f"Unexpected error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
# print (get_messages_for_user(connection("schooldata3"),232323,"student",242424,"student")


def send_message(connection, sender_id, sender_type, receiver_id, receiver_type, message, reply_to_message_id=None):
    """
    Send a new message and insert it into the messages table.
    
    Args:
        connection: MySQL connection object.
        sender_id: ID of the sender.
        sender_type: Type of the sender.
        receiver_id: ID of the receiver.
        receiver_type: Type of the receiver.
        message: The message content.
        reply_to_message_id: Optional ID of the message being replied to.
    
    Returns:
        bool: True if message sent successfully, False otherwise.
    """
    cursor = None
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            
            insert_query = """
            INSERT INTO messages (sender_id, sender_type, receiver_id, receiver_type, message, reply_to_message_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (sender_id, sender_type, receiver_id, receiver_type, message, reply_to_message_id)
            cursor.execute(insert_query, params)
            connection.commit()
            
            print(f"Message sent from {sender_type}:{sender_id} to {receiver_type}:{receiver_id}")
            return True
            
    except mysql.connector.Error as err:
        logging.error(f"Database error in send_message: {str(err)}")
        print(f"Error: {err}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in send_message: {str(e)}")
        print(f"Unexpected error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()



# send_message(connection("schooldata3"),232323,"student",242424,"student","hello2",None)



def get_teachers_with_shared_classes(teacher_code, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        # جلب accessible_classes للمعلم الحالي
        query_current = "SELECT accessible_classes FROM teachers WHERE code = %s"
        cursor.execute(query_current, (teacher_code,))
        current_res = cursor.fetchone()
        if not current_res or not current_res['accessible_classes']:
            logging.error(f"No accessible classes found for teacher {teacher_code}")
            return []
        
        # تحليل accessible_classes
        try:
            current_classes = json.loads(current_res['accessible_classes'])
        except json.JSONDecodeError:
            cleaned = re.sub(r'[\[\]\s\'"]', '', current_res['accessible_classes']).strip()
            current_classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
        
        # جلب جميع المعلمين الآخرين
        query_others = "SELECT code, name, accessible_classes FROM teachers WHERE code != %s"
        cursor.execute(query_others, (teacher_code,))
        others = cursor.fetchall()
        
        shared_teachers = []
        for other in others:
            try:
                other_classes = json.loads(other['accessible_classes'])
            except json.JSONDecodeError:
                cleaned = re.sub(r'[\[\]\s\'"]', '', other['accessible_classes']).strip()
                other_classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
            
            # تحقق من تداخل الفصول
            if set(current_classes) & set(other_classes):  # إذا كان هناك فصل مشترك
                shared_teachers.append({
                    'code': other['code'],
                    'name': bleach.clean(other['name']),
                    'type': 'teacher'
                })
        
        logging.info(f"Fetched {len(shared_teachers)} shared teachers for teacher {teacher_code}")
        return shared_teachers
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_teachers_with_shared_classes: {str(err)}")
        return []
    finally:
        cursor.close()

def get_headteacher_data(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT code, name FROM manager LIMIT 1"  # افتراضي سجل واحد
        cursor.execute(query)
        res = cursor.fetchone()
        if res:
            logging.info("Fetched headteacher data successfully")
            return {
                'code': res['code'],
                'name': bleach.clean(res['name']),
                'type': 'headteacher'
            }
        logging.error("No headteacher found")
        return None
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_headteacher_data: {str(err)}")
        return None
    finally:
        cursor.close()

def is_valid_teacher_contact(teacher_code, contact_code, contact_type, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        # جلب accessible_classes للمعلم
        query_teacher = "SELECT accessible_classes FROM teachers WHERE code = %s"
        cursor.execute(query_teacher, (teacher_code,))
        teacher_res = cursor.fetchone()
        if not teacher_res:
            logging.error(f"Teacher {teacher_code} not found")
            return False
        
        try:
            accessible_classes = json.loads(teacher_res['accessible_classes'])
        except json.JSONDecodeError:
            cleaned = re.sub(r'[\[\]\s\'"]', '', teacher_res['accessible_classes']).strip()
            accessible_classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
        
        if contact_type == 'student':
            # تحقق إذا كان الطالب في فصل من accessible_classes
            for class_name in accessible_classes:
                try:
                    query_student = f"SELECT code FROM {class_name} WHERE code = %s"
                    cursor.execute(query_student, (contact_code,))
                    if cursor.fetchone():
                        logging.info(f"Valid student contact {contact_code} for teacher {teacher_code}")
                        return True
                except mysql.connector.Error:
                    continue
            return False
        
        elif contact_type == 'parent':
            # جلب student_code للولي الأمر، ثم تحقق إذا كان الطالب في فصل
            query_parent = "SELECT student_code FROM parents WHERE student_code = %s"  # افترض أن contact_code هو id الولي
            cursor.execute(query_parent, (contact_code,))
            parent_res = cursor.fetchone()
            if not parent_res:
                return False
            student_code = parent_res['student_code']
            return is_valid_teacher_contact(teacher_code, student_code, 'student', conn)  # إعادة استخدام
        
        elif contact_type == 'teacher':
            # تحقق من فصل مشترك
            shared = get_teachers_with_shared_classes(teacher_code, conn)
            return any(t['code'] == contact_code for t in shared)
        
        elif contact_type == 'headteacher':
            # تحقق من وجود المدير
            ht = get_headteacher_data(conn)
            return ht and ht['code'] == contact_code
        
        logging.error(f"Invalid contact type {contact_type} for teacher {teacher_code}")
        return False
    except mysql.connector.Error as err:
        logging.error(f"Database error in is_valid_teacher_contact: {str(err)}")
        return False
    finally:
        cursor.close()




def get_teachers_for_headteacher(conn):
    """
    جلب قائمة جميع المعلمين للمدير
    """
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT code, name FROM teachers"
        cursor.execute(query)
        teachers = cursor.fetchall()
        return [{'code': t['code'], 'name': bleach.clean(t['name']), 'type': 'teacher'} for t in teachers]
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_teachers_for_headteacher: {str(err)}")
        return []
    finally:
        cursor.close()

def is_valid_headteacher_contact(headteacher_code, contact_code, contact_type, conn):
    """
    التحقق مما إذا كان المدير يمكنه التواصل مع جهة معينة (معلمين فقط)
    """
    cursor = conn.cursor(dictionary=True)
    try:
        if contact_type == 'teacher':
            query = "SELECT code FROM teachers WHERE code = %s"
            cursor.execute(query, (contact_code,))
            return bool(cursor.fetchone())
        return False
    except mysql.connector.Error as err:
        logging.error(f"Database error in is_valid_headteacher_contact: {str(err)}")
        return False
    finally:
        cursor.close()



def get_class_name_for_student(student_code, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        # افترض list من الفصول الممكنة (يمكن جلبها من teachers accessible_classes لكن للبساطة)
        possible_classes = []  # جمع من teachers
        query_teachers = "SELECT accessible_classes FROM teachers"
        cursor.execute(query_teachers)
        teachers = cursor.fetchall()
        for t in teachers:
            try:
                classes = json.loads(t['accessible_classes'])
            except json.JSONDecodeError:
                cleaned = re.sub(r'[\[\]\s\'"]', '', t['accessible_classes']).strip()
                classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
            possible_classes.extend(classes)
        possible_classes = list(set(possible_classes))  # unique
        
        for class_name in possible_classes:
            if not re.match(r'^[a-zA-Z0-9_]+$', class_name):
                continue  # skip invalid
            try:
                query = f"SELECT code FROM {class_name} WHERE code = %s"
                cursor.execute(query, (student_code,))
                if cursor.fetchone():
                    logging.info(f"Found class {class_name} for student {student_code}")
                    return class_name
            except mysql.connector.Error:
                continue
        logging.error(f"No class found for student {student_code}")
        return None
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_class_name_for_student: {str(err)}")
        return None
    finally:
        cursor.close()
 




















def get_existing_conversations_for_parent(student_code, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT DISTINCT receiver_id AS contact_id, receiver_type AS contact_type
        FROM messages
        WHERE sender_id = %s AND sender_type = 'parent'
        UNION
        SELECT DISTINCT sender_id AS contact_id, sender_type AS contact_type
        FROM messages
        WHERE receiver_id = %s AND receiver_type = 'parent'
        """
        cursor.execute(query, (student_code, student_code))
        conversations = cursor.fetchall()
        
        # جلب names (لـ teachers فقط)
        contacts = []
        for conv in conversations:
            if conv['contact_type'] == 'teacher':
                query_name = "SELECT name FROM teachers WHERE code = %s"
                cursor.execute(query_name, (conv['contact_id'],))
                res = cursor.fetchone()
                if res:
                    # جلب آخر رسالة
                    last_msg_query = """
                    SELECT message, created_at FROM messages 
                    WHERE (sender_id = %s AND sender_type = 'parent' AND receiver_id = %s AND receiver_type = 'teacher')
                    OR (sender_id = %s AND sender_type = 'teacher' AND receiver_id = %s AND receiver_type = 'parent')
                    ORDER BY created_at DESC LIMIT 1
                    """
                    cursor.execute(last_msg_query, (student_code, conv['contact_id'], conv['contact_id'], student_code))
                    last_msg = cursor.fetchone()
                    
                    contacts.append({
                        'contact_code': conv['contact_id'],
                        'contact_name': bleach.clean(res['name']),
                        'contact_type': 'teacher',
                        'last_message': bleach.clean(last_msg['message']) if last_msg else 'No messages yet',
                        'created_at': last_msg['created_at'] if last_msg else datetime.now()
                    })
        return contacts
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_existing_conversations_for_parent: {str(err)}")
        return []
    finally:
        cursor.close()

def is_valid_parent_contact(student_code, contact_code, contact_type, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        if contact_type != 'teacher':
            logging.error(f"Invalid contact type for parent: {contact_type}")
            return False
        
        # جلب class_name من student_code
        class_name = get_class_name_for_student(student_code, conn)
        if not class_name:
            logging.error(f"No class found for student {student_code}")
            return False
        
        # تحقق إذا كان المعلم يدرس الفصل
        query_teacher = "SELECT accessible_classes FROM teachers WHERE code = %s"
        cursor.execute(query_teacher, (contact_code,))
        teacher_res = cursor.fetchone()
        if not teacher_res:
            logging.error(f"Teacher {contact_code} not found")
            return False
        
        try:
            classes = json.loads(teacher_res['accessible_classes'])
        except json.JSONDecodeError:
            cleaned = re.sub(r'[\[\]\s\'"]', '', teacher_res['accessible_classes']).strip()
            classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
        
        if class_name in classes:
            logging.info(f"Valid teacher contact {contact_code} for parent of student {student_code}")
            return True
        return False
    except mysql.connector.Error as err:
        logging.error(f"Database error in is_valid_parent_contact: {str(err)}")
        return False
    finally:
        cursor.close()





def get_teachers_for_parent(student_code, conn):
    cursor = conn.cursor(dictionary=True)
    try:
        class_name = get_class_name_for_student(student_code, conn)
        if not class_name:
            return []
        
        query = "SELECT code, name, accessible_classes FROM teachers"
        cursor.execute(query)
        teachers = cursor.fetchall()
        
        valid_teachers = []
        for teacher in teachers:
            try:
                classes = json.loads(teacher['accessible_classes'])
            except json.JSONDecodeError:
                cleaned = re.sub(r'[\[\]\s\'"]', '', teacher['accessible_classes']).strip()
                classes = [cls.strip() for cls in cleaned.split(',') if cls.strip()]
            
            if class_name in classes:
                valid_teachers.append({
                    'code': teacher['code'],
                    'name': bleach.clean(teacher['name']),
                    'type': 'teacher'
                })
        
        logging.info(f"Fetched {len(valid_teachers)} teachers for parent of student {student_code}")
        return valid_teachers
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_teachers_for_parent: {str(err)}")
        return []
    finally:
        cursor.close()





def get_all_classes(conn):
    """Get all class tables excluding evaluations/notifications/videos."""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'class%'")
    all_tables = [t[0] for t in cursor.fetchall()]
    classes = [t for t in all_tables if not t.endswith(('_evaluations', '_notifications', '_videos'))]
    cursor.close()
    return classes





def get_classes_for_grade(classes, grade):
    """Filter classes for a specific grade."""
    return [cls for cls in classes if cls.startswith(f'class{grade}_')]





def get_attendance_data(conn, classes, start_date, end_date):
    """Fetch and process attendance for given classes and date range."""
    all_attendance = []
    for class_name in classes:
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM `{class_name}`"
        cursor.execute(query)
        students = cursor.fetchall()
        for student in students:
            attendance = process_attendance_data(student)
            filtered = [entry for entry in attendance if start_date <= datetime.strptime(entry['date'], '%Y-%m-%d').date() <= end_date]
            all_attendance.append({
                'class': class_name,
                'code': student.get('code'),
                'name': student.get('name', 'Unknown'),
                'attendance': filtered
            })
        cursor.close()
    return all_attendance





def calculate_statistics(attendance_data):
    """Calculate attendance statistics."""
    if not attendance_data:
        return {}, [], [], [], [], {}, {}

    total_sessions = 0
    total_present = 0
    student_absences = {}
    daily_presence = {}
    trend_rates = {}

    for student in attendance_data:
        code = student['code']
        student_absences[code] = {'name': student['name'], 'absences': 0}
        for entry in student['attendance']:
            date = entry['date']
            status = entry['status']
            
            total_sessions += 1
            if status == 'Present':
                total_present += 1
            else:
                student_absences[code]['absences'] += 1
            
            # Daily
            if date not in daily_presence:
                daily_presence[date] = {'present': 0, 'total': 0}
            daily_presence[date]['total'] += 1
            if status == 'Present':
                daily_presence[date]['present'] += 1
            
            # Trend (cumulative)
            if date not in trend_rates:
                trend_rates[date] = {'present': 0, 'total': 0}
            trend_rates[date]['total'] += 1
            if status == 'Present':
                trend_rates[date]['present'] += 1

    attendance_rate = (total_present / total_sessions * 100) if total_sessions > 0 else 0
    
    # Top absent
    top_absent = sorted(student_absences.items(), key=lambda x: x[1]['absences'], reverse=True)[0][1] if student_absences else None
    
    # Average daily
    daily_rates = {date: (data['present'] / data['total'] * 100) for date, data in daily_presence.items()}
    average_daily = sum(daily_rates.values()) / len(daily_rates) if daily_rates else 0
    
    # Pie data
    pie_data = [total_present, total_sessions - total_present]
    
    # Trend (sorted dates)
    sorted_dates = sorted(trend_rates.keys())
    trend_labels = sorted_dates
    trend_rates_list = [(trend_rates[date]['present'] / trend_rates[date]['total'] * 100) for date in sorted_dates]
    
    # Daily labels and rates
    daily_labels = sorted(daily_presence.keys())
    daily_rates_list = [daily_rates[date] for date in daily_labels]

    return {
        'total_sessions': total_sessions,
        'attendance_rate': round(attendance_rate, 2),
        'top_absent_student': top_absent,
        'average_daily_attendance': round(average_daily, 2),
        'pie_data': pie_data,
        'daily_labels': daily_labels,
        'daily_rates': daily_rates_list,
        'trend_labels': trend_labels,
        'trend_rates': trend_rates_list
    }