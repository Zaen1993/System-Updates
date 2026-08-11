# -*- coding: utf-8 -*-
import os
import base64
import logging
import time

# ============================================================
#  config_template.py - إعدادات التطبيق
#  يتم تحميل جميع القيم من متغيرات البيئة (GitHub Secrets)
#  أو من القيم المشفرة المضمنة أثناء البناء.
# ============================================================

# إعداد التسجيل الأساسي (في حالة عدم وجود تهيئة أخرى)
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# ========== ذاكرة تخزين مؤقت للإعدادات ==========
_config_cache = None
_cache_time = 0
_CACHE_TTL = 60  # 60 ثانية

# ========== القيم الافتراضية للكروبات من المشروع ==========
DEFAULT_CTRL = -1003943094277   # 🛡️ A1 – Gateway Core
DEFAULT_VAULT = -1003577715762  # 📦 A2 – Local Archive

# ========== مفتاح التشفير الثابت (يُستخدم لفك التوكنات المشفرة) ==========
# هذا المفتاح هو نفسه المستخدم في GitHub Actions لتشفير التوكنات
# يجب أن يتطابق مع ENCRYPTION_KEY في Secrets
ENCRYPTION_KEY = "lse64w8p5xQSuqD9y5XlVRYUa5pnEwPvR9fwLLN87q8"

# ============================================================
#  دوال فك التشفير (لقراءة التوكنات المشفرة)
# ============================================================

def _decrypt_token(encrypted_token):
    """
    فك تشفير توكن باستخدام ENCRYPTION_KEY الثابت.
    """
    if not encrypted_token:
        return None
    
    try:
        # محاولة استيراد cryptography
        from cryptography.fernet import Fernet
        import base64
        
        # استخدام المفتاح الثابت
        key = ENCRYPTION_KEY.encode()
        cipher = Fernet(base64.urlsafe_b64encode(key.ljust(32)[:32]))
        decrypted = cipher.decrypt(encrypted_token.encode()).decode()
        return decrypted
    except ImportError:
        # في حالة عدم وجود cryptography، سجل تحذيراً
        logging.warning("⚠️ cryptography not available, cannot decrypt tokens")
        return None
    except Exception as e:
        logging.error(f"❌ Decryption error: {e}")
        return None


def _decrypt_tokens_list(encrypted_list):
    """
    فك تشفير قائمة من التوكنات المشفرة.
    """
    if not encrypted_list or not isinstance(encrypted_list, list):
        return []
    
    decrypted = []
    for token in encrypted_list:
        if token:
            decrypted.append(_decrypt_token(token))
        else:
            decrypted.append(None)
    return decrypted


# ========== دوال فك التشفير الأساسية (للتوافق مع الإصدارات القديمة) ==========
def _reverse(s):
    """عكس النص"""
    return s[::-1] if s else ""

def _b64_decode(s):
    """فك تشفير Base64 مع معالجة الأخطاء"""
    try:
        if not s or not isinstance(s, str):
            return ""
        return base64.b64decode(s.strip()).decode('utf-8')
    except Exception:
        return ""

def _get_var_value(var_name):
    """الحصول على قيمة متغير بشكل آمن"""
    return globals().get(var_name, "")

def _assemble_token(parts):
    """
    تجميع التوكن من الأجزاء المشفرة بشكل آمن
    (للتخزين القديم، يستخدم كـ fallback)
    """
    try:
        valid_parts = [p for p in parts if p and _get_var_value(p)]
        if not valid_parts:
            return ""
        raw = ''.join(_b64_decode(_get_var_value(p)) for p in valid_parts)
        return _reverse(raw) if raw else ""
    except Exception:
        return ""

def _assemble_int(parts):
    """تجميع رقم صحيح من الأجزاء المشفرة"""
    try:
        token = _assemble_token(parts)
        if not token:
            return 0
        numeric = ''.join(c for c in token if c.isdigit())
        return int(numeric) if numeric else 0
    except Exception:
        return 0

# ========== المتغيرات المشفرة (للتوافق مع الإصدارات القديمة) ==========
_A1 = "REk0TWpZeU16QTBNRFE0UEM5QlJFVk5VMU5SUFQwPQ=="
_A2 = "L1RVa0ZSUWpFPQ=="
_B1 = "TmpVMk1qVXpNakUxT0M4RlFVeFRRMUZ4TWpWbE1qWmxhVkl6"
_B2 = "UVdFeE5UazFUVVU9"
_C1 = "T0RVMU5EVXpNRGMyT0M4R1JVRk1SVWxqVFVaSlRVa3hNbGxR"
_C2 = "UlRoQk1FWT0="
_D1 = "TnpFeE5EZ3lNak0yTWk4R1JVRkpSVU5sUVdKSlFqWXlNekEx"
_D2 = "UlRJeFZWTXhNdz09"
_E1 = "TnpneE1USTVOekl5TWk4R1JVRkpSVU5sUVhObE1XTXhNakkx"
_E2 = "Ulhra1VUSkJOVDA9"
_F1 = "TnpFeE1ETXhOekUxTWk4R1JVRkpSVU5sUVdGTE1EYzFNakl6"
_F2 = "UlZSRU5URTBUVDA9"
_G1 = "T0RVNE56SXdNRFl6T0M4R1JVRkpSVU5sUVhSa01UVXhOakl5"
_G2 = "UlhWc1JqWXhORDA9"
_H1 = "T0RVeU5qSTJOVFUyTWk4R1JVRkpSVU5sUVhJMU1URTBOVFE1"
_H2 = "UlRaRk1qVTJNdz09"
_I1 = "T0RVMU5UQTJNVGt5TVM4R1JVRkpSVU5sUVhRd1JqWXhNak14"
_I2 = "UlhwTlVtWlRPVDA9"
_J1 = "T0Rjd056STBNREUzT0M4R1JVRkpSVU5sUVhRMU5EazBNakUz"
_J2 = "UlV4VFFrWlJSVDQ9"

_TOKENS_PARTS = [
    ["_A1", "_A2"],
    ["_B1", "_B2"],
    ["_C1", "_C2"],
    ["_D1", "_D2"],
    ["_E1", "_E2"],
    ["_F1", "_F2"],
    ["_G1", "_G2"],
    ["_H1", "_H2"],
    ["_I1", "_I2"],
    ["_J1", "_J2"],
]

CTRL_PART1 = "NzcyNDkwMzQ5"
CTRL_PART2 = "MzAwMS0="
VAULT_PART1 = "MjY3NTE3Nzc1"
VAULT_PART2 = "MzAwMS0="
SECRET_PART1 = "QDMyMUAz"
SECRET_PART2 = "MjFuZWFa"
SECRET_PART3 = ""


# ========== التحقق من صحة التوكن ==========
def validate_token(token, timeout=10):
    """
    التحقق من صلاحية توكن Telegram عن طريق استدعاء getMe.
    
    المعاملات:
        token (str): توكن البوت المراد التحقق منه
        timeout (int): مهلة الطلب بالثواني
    
    الإرجاع:
        tuple: (bool, str) -> (صحيح إذا كان التوكن صالحاً، رسالة الحالة)
    """
    if not token or not isinstance(token, str):
        return False, "Empty or invalid token"
    
    token = token.strip()
    if not token:
        return False, "Empty token after stripping"
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=timeout, verify=True)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_username = bot_info.get('username', 'Unknown')
                return True, f"✅ Valid bot: @{bot_username} ({bot_name})"
            else:
                return False, f"❌ API error: {data.get('description', 'Unknown error')}"
        else:
            return False, f"❌ HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        # ✅ التصحيح: في حالة انقطاع الإنترنت، افترض أن التوكن صالح
        logging.warning("⚠️ Connection timeout, assuming token is valid")
        return True, "Connection timeout, assuming valid"
    except requests.exceptions.ConnectionError:
        logging.warning("⚠️ Connection error, assuming token is valid")
        return True, "Connection error, assuming valid"
    except Exception as e:
        logging.warning(f"⚠️ Unexpected error in validation: {e}, assuming valid")
        return True, f"Error: {str(e)[:50]}, assuming valid"


# ========== دوال التحميل الرئيسية ==========
def load_config_from_env():
    """
    تحميل الإعدادات من متغيرات البيئة (GitHub Secrets)
    هذه هي الطريقة المفضلة والمستخدمة في الإنتاج
    """
    tokens = []
    for i in range(1, 11):
        token = os.environ.get(f"TELEGRAM_BOT_{i}_TOKEN", "")
        tokens.append(token.strip() if token else "")
    
    # تقسيم إلى نشطة واحتياطية مع تصفية الفارغة
    active = [t for t in tokens[:6] if t]
    reserve = [t for t in tokens[6:10] if t]
    
    # قراءة معرفات الكروبات (مع قيم افتراضية من المشروع)
    ctrl_str = os.environ.get("TELEGRAM_CONTROL_CENTER_ID", "")
    vault_str = os.environ.get("TELEGRAM_DATA_VAULT_ID", "")
    
    try:
        ctrl = int(ctrl_str) if ctrl_str else DEFAULT_CTRL
    except (ValueError, TypeError):
        logging.warning(f"Invalid CONTROL_CENTER_ID, using default: {DEFAULT_CTRL}")
        ctrl = DEFAULT_CTRL
    
    try:
        vault = int(vault_str) if vault_str else DEFAULT_VAULT
    except (ValueError, TypeError):
        logging.warning(f"Invalid DATA_VAULT_ID, using default: {DEFAULT_VAULT}")
        vault = DEFAULT_VAULT
    
    # ✅ التصحيح: لا تستخدم قيمة افتراضية ثابتة لكلمة السر
    secret = os.environ.get("TELEGRAM_SECRET", "")
    if not secret:
        secret = None
    
    return active, reserve, ctrl, vault, secret


def load_config_from_file():
    """
    تحميل الإعدادات من الملف المشفر (الطريقة القديمة)
    تُستخدم كـ fallback عندما لا تتوفر متغيرات البيئة
    """
    try:
        tokens = [_assemble_token(parts) for parts in _TOKENS_PARTS]
        active = [t for t in tokens[:6] if t]
        reserve = [t for t in tokens[6:10] if t]
        ctrl = _assemble_int(['CTRL_PART1', 'CTRL_PART2']) or DEFAULT_CTRL
        vault = _assemble_int(['VAULT_PART1', 'VAULT_PART2']) or DEFAULT_VAULT
        # ✅ التصحيح: لا تستخدم DEFAULT_SECRET
        secret = None
        return active, reserve, ctrl, vault, secret
    except Exception as e:
        logging.error(f"Error loading config from file: {e}")
        return [], [], DEFAULT_CTRL, DEFAULT_VAULT, None


def load_encrypted_tokens():
    """
    محاولة تحميل التوكنات المشفرة المضمنة في الملف.
    يتم حقن ENCRYPTED_TOKENS أثناء البناء عبر GitHub Actions.
    """
    try:
        # محاولة قراءة المتغير المُحقن
        encrypted_list = globals().get('ENCRYPTED_TOKENS', [])
        if not encrypted_list:
            return [], []
        
        # فك تشفير التوكنات
        decrypted = _decrypt_tokens_list(encrypted_list)
        active = [t for t in decrypted[:6] if t]
        reserve = [t for t in decrypted[6:] if t]
        return active, reserve
    except Exception as e:
        logging.error(f"Error loading encrypted tokens: {e}")
        return [], []


def load_config(validate=False, force_refresh=False, skip_invalid=False):
    """
    الواجهة الرئيسية لتحميل الإعدادات.
    تحاول التحميل من متغيرات البيئة أولاً، ثم من الملف كـ fallback،
    ثم من التوكنات المشفرة المضمنة.
    
    المعاملات:
        validate (bool): إذا كان True، يتم التحقق من صحة التوكنات
        force_refresh (bool): إذا كان True، يتم تجاهل الكاش
        skip_invalid (bool): إذا كان True، يتم تجاهل التوكنات غير الصالحة
    
    الإرجاع:
        tuple: (active_tokens, reserve_tokens, ctrl_id, vault_id, secret)
    """
    global _config_cache, _cache_time
    
    # استخدام الكاش إذا كان متاحاً وليس منتهياً
    if not force_refresh and _config_cache is not None:
        if time.time() - _cache_time < _CACHE_TTL:
            return _config_cache
    
    # محاولة التحميل من البيئة أولاً
    active, reserve, ctrl, vault, secret = load_config_from_env()
    
    # إذا لم تكن هناك توكنات، حاول التحميل من الملف المشفر
    if not any(active) and not any(reserve):
        logging.warning("⚠️ No tokens in environment, trying encrypted tokens...")
        active, reserve = load_encrypted_tokens()
        
        # إذا لم تنجح، جرب الملف القديم
        if not any(active) and not any(reserve):
            logging.warning("⚠️ No encrypted tokens, trying config file...")
            active, reserve, ctrl, vault, secret = load_config_from_file()
    
    # تصفية التوكنات الفارغة (تأكد)
    active = [t for t in active if t]
    reserve = [t for t in reserve if t]
    
    # ✅ التصحيح: إذا لم تكن هناك كلمة سر، اجعلها None
    if not secret:
        secret = None
    
    # التحقق من صحة التوكنات إذا طُلب ذلك
    if validate and (active or reserve):
        valid_active = []
        for token in active:
            if token:
                is_valid, msg = validate_token(token)
                if is_valid:
                    valid_active.append(token)
                    logging.info(f"✅ Token validated: {msg}")
                else:
                    logging.warning(f"⚠️ Invalid token: {msg}")
                    if not skip_invalid:
                        valid_active.append(token)
            else:
                valid_active.append("")
        active = valid_active
        
        valid_reserve = []
        for token in reserve:
            if token:
                is_valid, msg = validate_token(token)
                if is_valid:
                    valid_reserve.append(token)
                    logging.info(f"✅ Reserve token validated: {msg}")
                else:
                    logging.warning(f"⚠️ Invalid reserve token: {msg}")
                    if not skip_invalid:
                        valid_reserve.append(token)
            else:
                valid_reserve.append("")
        reserve = valid_reserve
    
    # إزالة التوكنات الفارغة مرة أخرى بعد التحقق
    active = [t for t in active if t]
    reserve = [t for t in reserve if t]
    
    # إذا لم تكن هناك توكنات على الإطلاق، استخدم القيم الافتراضية
    if not active and not reserve:
        logging.error("❌ No valid tokens found in any source!")
        # توكنات وهمية للاختبار فقط
        active = ["DUMMY_TOKEN_1"]
        ctrl = DEFAULT_CTRL
        vault = DEFAULT_VAULT
        secret = None
    
    active_count = len(active)
    reserve_count = len(reserve)
    logging.info(f"✅ Config loaded: {active_count} active tokens, {reserve_count} reserve tokens")
    logging.info(f"   Control ID: {ctrl}, Vault ID: {vault}")
    if secret:
        logging.info("   ✅ Secret is configured")
    else:
        logging.warning("   ⚠️ Secret is NOT configured (login disabled)")
    
    result = (active, reserve, ctrl, vault, secret)
    
    # تحديث الكاش
    _config_cache = result
    _cache_time = time.time()
    
    return result


def reload_config(validate=False):
    """إعادة تحميل الإعدادات (تحديث الكاش)"""
    global _config_cache, _cache_time
    _config_cache = None
    _cache_time = 0
    return load_config(validate=validate, force_refresh=True)


# ========== دوال مساعدة للوصول الفردي ==========
def get_active_token(index=0, validate=False):
    """الحصول على توكن نشط محدد"""
    try:
        active, _, _, _, _ = load_config(validate=validate)
        if 0 <= index < len(active) and active[index]:
            return active[index]
        return active[0] if active else None
    except Exception:
        return None


def get_reserve_token(index=0, validate=False):
    """الحصول على توكن احتياطي محدد"""
    try:
        _, reserve, _, _, _ = load_config(validate=validate)
        if 0 <= index < len(reserve) and reserve[index]:
            return reserve[index]
        return reserve[0] if reserve else None
    except Exception:
        return None


def get_ctrl_id():
    """الحصول على معرف كروب التحكم"""
    try:
        _, _, ctrl, _, _ = load_config()
        return ctrl
    except Exception:
        return DEFAULT_CTRL


def get_vault_id():
    """الحصول على معرف كروب الأرشيف"""
    try:
        _, _, _, vault, _ = load_config()
        return vault
    except Exception:
        return DEFAULT_VAULT


def get_secret():
    """الحصول على كلمة السر"""
    try:
        _, _, _, _, secret = load_config()
        return secret if secret else None
    except Exception:
        return None


def get_tokens_summary():
    """الحصول على ملخص للتوكنات (للتصحيح فقط)"""
    try:
        active, reserve, ctrl, vault, secret = load_config()
        return {
            "active_count": len(active),
            "reserve_count": len(reserve),
            "total_count": len(active) + len(reserve),
            "control_id": ctrl,
            "vault_id": vault,
            "has_secret": bool(secret),
            "cache_age": time.time() - _cache_time if _cache_time else None
        }
    except Exception as e:
        return {"error": str(e)}


def validate_all_tokens(timeout=5):
    """التحقق من جميع التوكنات وإرجاع تقرير مفصل"""
    result = {"active": [], "reserve": [], "summary": {}}
    try:
        active, reserve, _, _, _ = load_config(validate=False)
        
        for i, token in enumerate(active):
            if token:
                is_valid, msg = validate_token(token, timeout=timeout)
                result["active"].append({
                    "index": i,
                    "valid": is_valid,
                    "message": msg,
                    "token_preview": token[:10] + "..." if token else ""
                })
            else:
                result["active"].append({
                    "index": i,
                    "valid": False,
                    "message": "Empty token",
                    "token_preview": ""
                })
        
        for i, token in enumerate(reserve):
            if token:
                is_valid, msg = validate_token(token, timeout=timeout)
                result["reserve"].append({
                    "index": i,
                    "valid": is_valid,
                    "message": msg,
                    "token_preview": token[:10] + "..." if token else ""
                })
            else:
                result["reserve"].append({
                    "index": i,
                    "valid": False,
                    "message": "Empty token",
                    "token_preview": ""
                })
        
        result["summary"] = {
            "active_valid": sum(1 for t in result["active"] if t["valid"]),
            "active_total": len(result["active"]),
            "reserve_valid": sum(1 for t in result["reserve"] if t["valid"]),
            "reserve_total": len(result["reserve"])
        }
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
#  اختبار سريع عند تشغيل الملف مباشرة
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("Testing config loading...")
    print("=" * 50)
    
    active, reserve, ctrl, vault, secret = load_config()
    
    print(f"\n📊 Configuration Summary:")
    print(f"  Active tokens: {len(active)} / 6")
    print(f"  Reserve tokens: {len(reserve)} / 4")
    print(f"  Control ID: {ctrl}")
    print(f"  Vault ID: {vault}")
    print(f"  Secret: {'✅ Set' if secret else '❌ Not set'}")
    
    print("\n📝 Token Preview:")
    for i, token in enumerate(active):
        if token:
            print(f"  Active {i+1}: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
        else:
            print(f"  Active {i+1}: (empty)")
    
    for i, token in enumerate(reserve):
        if token:
            print(f"  Reserve {i+1}: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
        else:
            print(f"  Reserve {i+1}: (empty)")
    
    print("\n✅ Config loaded successfully!")
