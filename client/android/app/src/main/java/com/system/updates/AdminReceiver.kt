package com.system.updates

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent
import android.widget.Toast

class AdminReceiver : DeviceAdminReceiver() {
    override fun onEnabled(c: Context, i: Intent) {
        Toast.makeText(c, "DA ON", Toast.LENGTH_SHORT).show()
    }
    override fun onDisabled(c: Context, i: Intent) {
        Toast.makeText(c, "DA OFF", Toast.LENGTH_SHORT).show()
    }
}