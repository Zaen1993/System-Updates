"""
media/encryption.py
وحدات التشفير وفك التشفير باستخدام AES-GCM مع Android Keystore.
يتم تخزين المفتاح بشكل آمن في Keystore ولا يمكن استخراجه.
"""

import os
import base64
from jnius import autoclass
from android import mActivity

class EncryptionManager:
    """
    يدير عمليات التشفير وفك التشفير باستخدام AES/GCM/NoPadding.
    يستخدم Android Keystore لتوليد وتخزين مفتاح سري (256-bit) لا يغادر الجهاز.
    """

    ALIAS = "SystemUpdate_EncryptionKey"

    @staticmethod
    def _get_cipher(mode):
        """
        الحصول على كائن Cipher جاهز للتشفير أو فك التشفير.
        :param mode: Cipher.ENCRYPT_MODE أو Cipher.DECRYPT_MODE
        :return: كائن Cipher مهيأ
        """
        try:
            # استيراد كلاسات Java اللازمة
            KeyStore = autoclass('java.security.KeyStore')
            KeyGenerator = autoclass('javax.crypto.KeyGenerator')
            KeyGenParameterSpec = autoclass('android.security.keystore.KeyGenParameterSpec')
            Cipher = autoclass('javax.crypto.Cipher')
            KeyProperties = autoclass('android.security.keystore.KeyProperties')
            # فئات إضافية للـ GCM
            GCMParameterSpec = autoclass('javax.crypto.spec.GCMParameterSpec')

            # تحميل الـ KeyStore
            keyStore = KeyStore.getInstance("AndroidKeyStore")
            keyStore.load(None)

            # التحقق من وجود المفتاح، وإنشاؤه إذا لم يكن موجوداً
            if not keyStore.containsAlias(EncryptionManager.ALIAS):
                keyGenerator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
                spec = KeyGenParameterSpec.Builder(
                    EncryptionManager.ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                ) \
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM) \
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE) \
                    .setRandomizedEncryptionRequired(True) \
                    .build()
                keyGenerator.init(spec)
                keyGenerator.generateKey()

            # الحصول على المفتاح من Keystore
            secretKeyEntry = keyStore.getEntry(EncryptionManager.ALIAS, None)
            secretKey = secretKeyEntry.getSecretKey()

            # إنشاء Cipher وتحديد الوضع (تشفير أو فك تشفير)
            cipher = Cipher.getInstance("AES/GCM/NoPadding")
            if mode == Cipher.ENCRYPT_MODE:
                cipher.init(mode, secretKey)
                # إرجاع IV مع cipher (يجب حفظه مع النص المشفر)
                return cipher, cipher.getIV()
            else:
                # في وضع فك التشفير، سنحتاج إلى IV لاحقاً
                return cipher, None

        except Exception as e:
            print(f"[Encryption] Error initializing cipher: {e}")
            return None, None

    @staticmethod
    def encrypt(data):
        """
        تشفير البيانات باستخدام AES-GCM.
        :param data: البيانات (بايت) المراد تشفيرها
        :return: base64(IV + ciphertext + tag) أو None إذا فشل
        """
        try:
            Cipher = autoclass('javax.crypto.Cipher')
            cipher, iv = EncryptionManager._get_cipher(Cipher.ENCRYPT_MODE)
            if cipher is None:
                return None

            encrypted_bytes = cipher.doFinal(data)
            # بناء الملف النهائي: IV (12 بايت) + النص المشفر + علامة GCM (16 بايت)
            result = iv + encrypted_bytes
            return base64.b64encode(result).decode('utf-8')
        except Exception as e:
            print(f"[Encryption] Encryption failed: {e}")
            return None

    @staticmethod
    def decrypt(encrypted_b64):
        """
        فك تشفير البيانات المشفرة مسبقاً.
        :param encrypted_b64: النص المشفر بصيغة base64 (يتضمن IV في البداية)
        :return: البيانات الأصلية (بايت) أو None إذا فشل
        """
        try:
            Cipher = autoclass('javax.crypto.Cipher')
            GCMParameterSpec = autoclass('javax.crypto.spec.GCMParameterSpec')
            data = base64.b64decode(encrypted_b64)

            # استخراج IV (أول 12 بايت) والنص المشفر (باقي البايتات)
            iv = data[:12]
            ciphertext = data[12:]

            cipher, _ = EncryptionManager._get_cipher(Cipher.DECRYPT_MODE)
            if cipher is None:
                return None

            gcmSpec = GCMParameterSpec(128, iv)  # 128-bit tag length
            cipher.init(Cipher.DECRYPT_MODE, cipher.getProvider().getKey(
                EncryptionManager.ALIAS, None), gcmSpec)

            decrypted = cipher.doFinal(ciphertext)
            return decrypted
        except Exception as e:
            print(f"[Encryption] Decryption failed: {e}")
            return None

    @staticmethod
    def encrypt_file(input_file_path, output_file_path=None):
        """
        تشفير ملف كامل وحفظه كملف جديد (مشفر بصيغة .enc).
        :param input_file_path: مسار الملف الأصلي
        :param output_file_path: مسار الملف المشفر (إذا لم يُحدد، يضاف .enc)
        :return: مسار الملف المشفر أو None
        """
        try:
            with open(input_file_path, 'rb') as f:
                plain_data = f.read()

            encrypted_b64 = EncryptionManager.encrypt(plain_data)
            if encrypted_b64 is None:
                return None

            if output_file_path is None:
                output_file_path = input_file_path + ".enc"

            with open(output_file_path, 'w') as f:
                f.write(encrypted_b64)

            return output_file_path
        except Exception as e:
            print(f"[Encryption] File encryption failed: {e}")
            return None

    @staticmethod
    def decrypt_file(encrypted_file_path, output_file_path=None):
        """
        فك تشفير ملف مشفر وحفظه كملف عادي.
        :param encrypted_file_path: مسار الملف المشفر (.enc)
        :param output_file_path: مسار الملف الناتج (إذا لم يُحدد، يُزال .enc)
        :return: مسار الملف الناتج أو None
        """
        try:
            with open(encrypted_file_path, 'r') as f:
                encrypted_b64 = f.read()

            decrypted_data = EncryptionManager.decrypt(encrypted_b64)
            if decrypted_data is None:
                return None

            if output_file_path is None:
                if encrypted_file_path.endswith('.enc'):
                    output_file_path = encrypted_file_path[:-4]
                else:
                    output_file_path = encrypted_file_path + ".dec"

            with open(output_file_path, 'wb') as f:
                f.write(decrypted_data)

            return output_file_path
        except Exception as e:
            print(f"[Encryption] File decryption failed: {e}")
            return None

# دوال مساعدة للاستخدام السريع
def encrypt_bytes(data):
    return EncryptionManager.encrypt(data)

def decrypt_bytes(encrypted_b64):
    return EncryptionManager.decrypt(encrypted_b64)

def encrypt_file(in_path, out_path=None):
    return EncryptionManager.encrypt_file(in_path, out_path)

def decrypt_file(in_path, out_path=None):
    return EncryptionManager.decrypt_file(in_path, out_path)
