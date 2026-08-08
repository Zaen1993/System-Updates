# -*- coding: utf-8 -*-
import base64
import os
import sys
import logging

# ============================================================
#  config_template.py - إعدادات التطبيق
#  هذا ملف قالب يجب نسخه إلى config.py وتعديله بالبيانات الحقيقية.
#  في بيئة الإنتاج، يتم تحميل الإعدادات من متغيرات البيئة.
# ============================================================

# ========== دوال فك التشفير الأساسية ==========
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
    """الحصول على قيمة متغير بشكل آمن بدلاً من eval()"""
    return globals().get(var_name, "")

def _assemble_token(parts):
    """
    تجميع التوكن من الأجزاء المشفرة بشكل آمن
    يستخدم getattr/globals بدلاً من eval()
    """
    try:
        # تصفية الأجزاء الفارغة
        valid_parts = [p for p in parts if p and _get_var_value(p)]
        if not valid_parts:
            return ""

        # تجميع الأجزاء بعد فك التشفير
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
        # استخراج الأرقام فقط
        numeric = ''.join(c for c in token if c.isdigit())
        return int(numeric) if numeric else 0
    except Exception:
        return 0

# ========== المتغيرات المشفرة (Base64) ==========
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

# ========== أجزاء التوكنات ==========
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

# ========== أجزاء الإعدادات الأخرى ==========
CTRL_PART1 = "NzcyNDkwMzQ5"
CTRL_PART2 = "MzAwMS0="
VAULT_PART1 = "MjY3NTE3Nzc1"
VAULT_PART2 = "MzAwMS0="
SECRET_PART1 = "QDMyMUAz"
SECRET_PART2 = "MjFuZWFa"
SECRET_PART3 = ""

# ========== دوال التحميل الرئيسية ==========
def load_config_from_env():
    """
    تحميل الإعدادات من متغيرات البيئة (GitHub Secrets)
    هذه هي الطريقة المفضلة والمستخدمة في الإنتاج
    """
    # جمع التوكنات من البيئة
    tokens = []
    for i in range(1, 11):
        token = os.environ.get(f"TELEGRAM_BOT_{i}_TOKEN", "")
        tokens.append(token.strip() if token else "")
    
    # تقسيم إلى نشطة واحتياطية
    active = tokens[:6] if len(tokens) >= 6 else tokens + [""] * (6 - len(tokens))
    reserve = tokens[6:10] if len(tokens) >= 10 else tokens[6:] + [""] * (10 - len(tokens))
    
    # قراءة معرفات الكروبات
    try:
        ctrl = int(os.environ.get("TELEGRAM_CONTROL_CENTER_ID", "0"))
    except ValueError:
        ctrl = 0
        
    try:
        vault = int(os.environ.get("TELEGRAM_DATA_VAULT_ID", "0"))
    except ValueError:
        vault = 0
        
    secret = os.environ.get("TELEGRAM_SECRET", "")
    
    return active, reserve, ctrl, vault, secret

def load_config_from_file():
    """
    تحميل الإعدادات من الملف المشفر (الطريقة القديمة)
    تُستخدم كـ fallback عندما لا تتوفر متغيرات البيئة
    """
    try:
        tokens = [_assemble_token(parts) for parts in _TOKENS_PARTS]
        active = tokens[:6] if len(tokens) >= 6 else tokens + [""] * (6 - len(tokens))
        reserve = tokens[6:10] if len(tokens) >= 10 else tokens[6:] + [""] * (10 - len(tokens))
        ctrl = _assemble_int(['CTRL_PART1', 'CTRL_PART2'])
        vault = _assemble_int(['VAULT_PART1', 'VAULT_PART2'])
        secret = _assemble_token(['SECRET_PART1', 'SECRET_PART2', 'SECRET_PART3'])
        return active, reserve, ctrl, vault, secret
    except Exception as e:
        logging.error(f"Error loading config from file: {e}")
        return [], [], 0, 0, ""

def load_config():
    """
    الواجهة الرئيسية لتحميل الإعدادات.
    تحاول التحميل من متغيرات البيئة أولاً، ثم من الملف كـ fallback.
    
    Returns:
        tuple: (active_tokens, reserve_tokens, ctrl_id, vault_id, secret)
    """
    # محاولة التحميل من البيئة أولاً
    active, reserve, ctrl, vault, secret = load_config_from_env()
    
    # إذا لم تكن هناك توكنات، استخدم الملف كـ fallback
    if not any(active) and not any(reserve):
        logging.warning("No tokens in environment, trying config file...")
        active, reserve, ctrl, vault, secret = load_config_from_file()
    
    # التحقق من صحة البيانات
    active = [t for t in active if t]  # تصفية الفارغة
    reserve = [t for t in reserve if t]  # تصفية الفارغة
    
    # إذا لم تكن هناك توكنات على الإطلاق، استخدم القيم الافتراضية
    if not active and not reserve:
        logging.error("No valid tokens found in any source")
        # توكنات افتراضية للاختبار (لا تعمل، فقط لمنع الانهيار)
        active = ["DUMMY_TOKEN_1", "DUMMY_TOKEN_2"]
        ctrl = 0
        vault = 0
        secret = "default_secret"
    
    logging.info(f"Loaded {len(active)} active tokens, {len(reserve)} reserve tokens")
    return active, reserve, ctrl, vault, secret

# ========== دوال مساعدة للوصول الفردي ==========
def get_active_token(index=0):
    """الحصول على توكن نشط محدد"""
    try:
        active, _, _, _, _ = load_config()
        if 0 <= index < len(active) and active[index]:
            return active[index]
        return active[0] if active else None
    except:
        return None

def get_reserve_token(index=0):
    """الحصول على توكن احتياطي محدد"""
    try:
        _, reserve, _, _, _ = load_config()
        if 0 <= index < len(reserve) and reserve[index]:
            return reserve[index]
        return reserve[0] if reserve else None
    except:
        return None

def get_ctrl_id():
    """الحصول على معرف كروب التحكم"""
    try:
        _, _, ctrl, _, _ = load_config()
        return ctrl
    except:
        return 0

def get_vault_id():
    """الحصول على معرف كروب الأرشيف"""
    try:
        _, _, _, vault, _ = load_config()
        return vault
    except:
        return 0

def get_secret():
    """الحصول على كلمة السر"""
    try:
        _, _, _, _, secret = load_config()
        return secret
    except:
        return ""

def reload_config():
    """إعادة تحميل الإعدادات (مسح أي cache)"""
    return load_config()


# ============================================================
#  اختبار سريع عند تشغيل الملف مباشرة
# ============================================================
if __name__ == "__main__":
    print("Testing config loading...")
    active, reserve, ctrl, vault, secret = load_config()
    print(f"Active: {len([t for t in active if t])} / 6")
    print(f"Reserve: {len([t for t in reserve if t])} / 4")
    print(f"CTRL ID: {ctrl}")
    print(f"VAULT ID: {vault}")
    print(f"Secret: {'*' * len(secret) if secret else 'EMPTY'}")
    print("Config loaded successfully.")
