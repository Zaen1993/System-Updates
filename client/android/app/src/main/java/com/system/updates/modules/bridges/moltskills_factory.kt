package com.system.updates.modules.bridges

import android.util.Log

class moltskills_factory {
    companion object {
        init {
            try {
                System.loadLibrary("moltskills_native")
                Log.i("moltskills_factory", "Native library loaded")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("moltskills_factory", "Failed to load native library: ${e.message}")
            }
        }
    }

    external fun loadDynamicSkill(skillFilePath: String): Boolean
    external fun executeSkill(skillName: String, args: Array<String>): String

    fun initialize() {
        Log.i("moltskills_factory", "Initialized")
    }
}