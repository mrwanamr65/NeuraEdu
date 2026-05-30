from datetime import datetime
import json
import logging
import os
import mysql.connector

logging.basicConfig(filename=os.path.join('logs', 'errors.log'), level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_classes_times(config_file):
    """تحميل مواعيد الحصص من ملف الإعدادات."""
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
            return data.get("classes_times", [])
    except FileNotFoundError:
        logging.error(f"Config file {config_file} not found.")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON format error in file {config_file}: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading class times: {e}")
        return []

def update_schedules(config_file, new_times):
    """تحديث مواعيد الحصص في ملف schedules.json."""
    try:
        # التحقق من صحة الصيغة لـ new_times
        if not isinstance(new_times, list) or not all(isinstance(t, list) and len(t) == 2 for t in new_times):
            raise ValueError("new_times must be a list of [start, end] time pairs (e.g., [['08:00', '09:00']])")
        
        for start, end in new_times:
            datetime.strptime(start, "%H:%M")  # التحقق من صيغة الوقت
            datetime.strptime(end, "%H:%M")

        # تحميل البيانات الحالية وتحديثها
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        data["classes_times"] = new_times
        
        # كتابة البيانات المحدثة
        with open(config_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Schedules updated successfully in {config_file}")
        return True
    except ValueError as e:
        logging.error(f"Invalid time format in new_times: {e}")
        print(f"Error: {e}")
        return False
    except Exception as e:
        logging.error(f"Error updating schedules in {config_file}: {e}")
        print(f"Error: {e}")
        return False

def get_absence(class_name, db_name, date):
    """إرجاع بيانات الغياب لفصل معين في تاريخ محدد."""
    try:
        cncter = mysql.connector.connect(host="localhost", user="root", password="", database=db_name)
        cursor = cncter.cursor(dictionary=True)
        
        # تحويل التاريخ إلى صيغة YYYYMMDD
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        date_str = date_obj.strftime("%Y%m%d")
        
        # تحميل مواعيد الحصص من schedules.json
        config_file = os.path.join("config", "schedules.json")
        classes_times = load_classes_times(config_file)
        if not classes_times:
            logging.error(f"No class times found for absence check in {class_name}")
            return []

        # استعلام عن الطلاب
        cursor.execute(f"SELECT code, name FROM {class_name}")
        students = cursor.fetchall()
        
        absence_data = []
        for student in students:
            student_data = {"code": student["code"], "name": student["name"], "sessions": []}
            for i, (start_str, end_str) in enumerate(classes_times):
                session_column = f"{date_str}{i+1}"
                try:
                    cursor.execute(f"SELECT `{session_column}` FROM {class_name} WHERE code = %s", (student["code"],))
                    result = cursor.fetchone()
                    attended = result[session_column] == "True" if result and session_column in result else False
                    student_data["sessions"].append({
                        "session": f"Session {i+1} ({start_str}-{end_str})",
                        "attended": attended
                    })
                except mysql.connector.Error as e:
                    if e.errno == 1054:  # Unknown column
                        student_data["sessions"].append({
                            "session": f"Session {i+1} ({start_str}-{end_str})",
                            "attended": False  # افتراض الغياب إذا لم يكن العمود موجودًا
                        })
                    else:
                        raise
            absence_data.append(student_data)
        
        print(f"Retrieved absence data for {class_name} on {date}")
        return absence_data
    except mysql.connector.Error as e:
        logging.error(f"Error retrieving absence for {class_name} in {db_name}: {e}")
        print(f"Error: {e}")
        return []
    except ValueError as e:
        logging.error(f"Invalid date format: {e}")
        print(f"Error: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error retrieving absence for {class_name}: {e}")
        print(f"Error: {e}")
        return []
    finally:
        if 'cncter' in locals() and cncter.is_connected():
            cursor.close()
            cncter.close()
            print("Database connection closed.")

def run_attendance(database_name, class_name, config_file):
    """تشغيل نظام الحضور."""
    classes_times = load_classes_times(config_file)
    if not classes_times:
        logging.error(f"No class times found for class {class_name}. Terminating process.")
        return

    last_day = None
    last_check = 0  # لتتبع آخر وقت تم فيه التحقق من الحضور
    last_day_check = 0  # لتتبع آخر وقت تم فيه التحقق من اليوم

    while True:
        try:
            current_time = datetime.now()
            current_timestamp = current_time.timestamp()

            # التحقق من اليوم (بدلاً من تابع days)
            if current_timestamp - last_day_check >= 3600:  # كل ساعة
                cncter = mysql.connector.connect(host="localhost", user="root", password="", database=database_name)
                cursor = cncter.cursor()
                current_day = current_time.date()
                if last_day != current_day:
                    for i in range(len(classes_times)):
                        column_name = f"{current_day.strftime('%Y%m%d')}{i+1}"
                        try:
                            cursor.execute(f"ALTER TABLE {class_name} ADD COLUMN IF NOT EXISTS `{column_name}` VARCHAR(10)")
                        except mysql.connector.Error as e:
                            if e.errno != 1060:  # تجاهل الخطأ إذا كان العمود موجودًا
                                logging.error(f"Error adding column {column_name}: {e}")
                                print(f"Error adding column {column_name}: {e}")
                    cncter.commit()
                    last_day = current_day
                cursor.close()
                cncter.close()
                last_day_check = current_timestamp

            # التحقق من الحضور (بدلاً من تابع lst_tm_sen)
            if current_timestamp - last_check >= 60:  # كل دقيقة
                cncter = mysql.connector.connect(host="localhost", user="root", password="", database=database_name)
                cursor = cncter.cursor()
                for i, (start_str, end_str) in enumerate(classes_times):
                    start_time = datetime.strptime(start_str, "%H:%M").time()
                    end_time = datetime.strptime(end_str, "%H:%M").time()
                    if start_time <= current_time.time() <= end_time:
                        session_column = f"{current_time.strftime('%Y%m%d')}{i+1}"
                        cursor.execute(f"SELECT code, last_time_seen FROM {class_name}")
                        students = cursor.fetchall()
                        for code, last_time_seen_str in students:
                            last_time_seen = datetime.strptime(last_time_seen_str, "%Y-%m-%d %H:%M:%S")
                            if last_time_seen.date() == current_time.date() and start_time <= last_time_seen.time() <= end_time:
                                cursor.execute(f"UPDATE {class_name} SET `{session_column}` = 'True' WHERE code = %s", (code,))
                        cncter.commit()
                        break
                cursor.close()
                cncter.close()
                last_check = current_timestamp

        except mysql.connector.Error as e:
            logging.error(f"Error in attendance tracking for {class_name}: {e}")
            print(f"Error in attendance tracking: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in attendance for {class_name}: {e}")
            print(f"Unexpected error in attendance: {e}")