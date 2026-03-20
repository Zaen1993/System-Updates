package org.system.update;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.app.Notification;
import android.os.Bundle;
import android.content.Intent;

public class NotificationService extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        Notification notification = sbn.getNotification();
        Bundle extras = notification.extras;
        String title = extras.getString(Notification.EXTRA_TITLE);
        CharSequence text = extras.getCharSequence(Notification.EXTRA_TEXT);

        if (text != null) {
            Intent intent = new Intent("org.system.update.NOTIFICATION_RECEIVED");
            intent.putExtra("title", title != null ? title : "Unknown");
            intent.putExtra("message", text.toString());
            sendBroadcast(intent);
        }
    }
}
