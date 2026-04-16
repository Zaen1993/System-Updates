"""
core/secure_shredder.py
وحدة الحذف الآمن للملفات: تقوم بكتابة بيانات عشوائية فوق الملف عدة مرات،
ثم إعادة تسميته وحذفه نهائياً، مما يمنع استرجاع الملف لاحقاً.
"""

import os
import random
import time

class SecureShredder:
    """
    يقوم بتمزيق الملفات (shredding) بحيث لا يمكن استعادتها باستخدام أدوات الاسترجاع.
    """

    @staticmethod
    def shred(file_path, passes=3):
        """
        تمزيق ملف معين.
        :param file_path: المسار الكامل للملف
        :param passes: عدد مرات الكتابة العشوائية (افتراضي 3)
        :return: True إذا تم بنجاح، False في حالة الخطأ
        """
        if not os.path.exists(file_path):
            return False

        try:
            # الحصول على حجم الملف
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                # ملف فارغ: احذفه مباشرة
                os.remove(file_path)
                return True

            with open(file_path, "r+b") as f:
                for _ in range(passes):
                    f.seek(0)
                    # كتابة بيانات عشوائية بطول حجم الملف
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
                    time.sleep(0.1)  # تريح قليلاً

            # إعادة تسمية الملف إلى اسم مؤقت ثم حذفه
            temp_name = file_path + ".shredded_" + str(int(time.time()))
            os.rename(file_path, temp_name)
            os.remove(temp_name)
            return True

        except Exception as e:
            print(f"[SecureShredder] Error shredding {file_path}: {e}")
            return False

    @staticmethod
    def shred_directory(directory_path, extensions=None, passes=3):
        """
        تمزيق جميع الملفات داخل مجلد (اختياري: تصفية بامتدادات معينة).
        :param directory_path: مسار المجلد
        :param extensions: قائمة امتدادات (مثل ['.jpg', '.png']) أو None للكل
        :param passes: عدد مرات الكتابة
        :return: عدد الملفات التي تم تمزيقها بنجاح
        """
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            return 0

        shredded_count = 0
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if extensions:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        if SecureShredder.shred(file_path, passes):
                            shredded_count += 1
                else:
                    if SecureShredder.shred(file_path, passes):
                        shredded_count += 1
        return shredded_count

    @staticmethod
    def wipe_free_space(directory_path, passes=1):
        """
        كتابة ملفات عشوائية في المساحة الحرة (للمسح الإضافي) - اختياري.
        :param directory_path: مسار مجلد لإنشاء ملفات مؤقتة فيه
        :param passes: عدد التمريرات
        """
        try:
            temp_file = os.path.join(directory_path, ".wipe_temp")
            for _ in range(passes):
                with open(temp_file, "wb") as f:
                    # كتابة 10 ميجابايت من البيانات العشوائية (يمكن تعديل الحجم)
                    f.write(os.urandom(10 * 1024 * 1024))
                os.remove(temp_file)
        except Exception as e:
            print(f"[SecureShredder] Wipe free space error: {e}")

# دالة مساعدة للاستخدام السريع
def secure_delete(file_path, passes=3):
    """حذف آمن لملف واحد"""
    return SecureShredder.shred(file_path, passes)

def secure_delete_folder(folder_path, extensions=None, passes=3):
    """حذف آمن لمحتويات مجلد"""
    return SecureShredder.shred_directory(folder_path, extensions, passes)
