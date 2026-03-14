# -*- coding: utf-8 -*-

MESSAGES = {
    "auth_required": "⚠️ الوصول مرفوض. يرجى تسجيل الدخول أولاً.",
    "auth_success": "✅ تم التحقق من الهوية بنجاح. مرحباً بك أيها المشرف.",
    "session_expired": "⌛ انتهت صلاحية الجلسة (10 دقائق). يرجى إعادة تسجيل الدخول للأمان.",
    "login_prompt": "🔑 يرجى إرسال كلمة المرور الخاصة بلوحة التحكم:",
    "new_device_connected": "📱 جهاز جديد متصل الآن!\nID: {device_id}\nالنظام: {os_version}",
    "device_disconnected": "🚫 انقطع الاتصال بالجهاز: {device_id}",
    "command_sent": "🚀 تم إرسال الأمر [{command}] إلى الجهاز بنجاح.",
    "command_failed": "❌ فشل إرسال الأمر إلى الجهاز. تأكد من حالة الاتصال.",
    "backup_start": "📦 جاري إنشاء نسخة احتياطية للنظام...",
    "backup_success": "✅ اكتملت النسخة الاحتياطية بنجاح في المسار:\n{path}",
    "backup_failed": "⚠️ فشل إنشاء النسخة الاحتياطية: {error}",
    "cleanup_done": "🧹 تم تنظيف النسخ القديمة (أقدم من {days} أيام).",
    "ai_generating": "🤖 الذكاء الاصطناعي يقوم بتحليل الثغرات وتوليد الأوامر...",
    "exploit_generated": "🎯 تم توليد ثغرة مخصصة لـ {device_id}\nالنوع: {vuln_type}\nنسبة النجاح: {confidence}%",
    "sync_complete": "☁️ تم مزامنة البيانات والنتائج مع قاعدة بيانات Supabase.",
    "status_ready": "🟢 النظام جاهز ويعمل الآن.",
    "status_offline": "🔴 النظام متوقف أو في وضع الأوفلاين.",
    "error_occurred": "❗ حدث خطأ غير متوقع: {error}",
    "help_menu": "🛠️ **قائمة أوامر التحكم:**\n/start - بدء الجلسة\n/status - حالة السيرفر\n/devices - عرض الأجهزة المتصلة\n/backup - إنشاء نسخة احتياطية فورية\n/logout - تسجيل الخروج"
}

def get_text(key, **kwargs):
    text = MESSAGES.get(key, f"Missing text: {key}")
    try:
        return text.format(**kwargs)
    except KeyError:
        return text
