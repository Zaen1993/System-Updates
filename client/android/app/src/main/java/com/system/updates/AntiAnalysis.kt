package com.system.updates

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Debug
import java.io.File

class AntiAnalysis {
    private var d=false
    private var e=false
    private var s=false

    fun ck(ctx:Context):Int{
        var sc=0
        if(dbg()) { d=true; sc+=1 }
        if(emu()) { e=true; sc+=2 }
        if(sec(ctx)) { s=true; sc+=4 }
        return sc
    }

    private fun dbg():Boolean{
        return Debug.isDebuggerConnected() || Debug.waitingForDebugger()
    }

    private fun emu():Boolean{
        val pf=listOf("goldfish","ranchu","vbox","qemu")
        val b=Build.HARDWARE.lowercase()
        for(p in pf) if(b.contains(p)) return true
        val fb=Build.FINGERPRINT.lowercase()
        if(fb.contains("generic") || fb.contains("emulator")) return true
        val m=Build.MANUFACTURER.lowercase()
        if(m.contains("genymotion") || m.contains("unknown")) return true
        return false
    }

    private fun sec(ctx:Context):Boolean{
        val ap=listOf("com.kms.free","com.avast.android","com.eset","com.symantec","com.mcafee")
        val pm=ctx.packageManager
        for(a in ap){
            try{
                pm.getPackageInfo(a,0)
                return true
            }catch(e:PackageManager.NameNotFoundException){}
        }
        val sf=File("/system/bin/su")
        if(sf.exists()) return true
        val xf=File("/system/xbin/su")
        if(xf.exists()) return true
        val mp=File("/system/app/Superuser.apk")
        if(mp.exists()) return true
        return false
    }

    fun hd(){
        if(d||e||s){
            android.os.Process.killProcess(android.os.Process.myPid())
        }
    }

    fun st():String{
        return when{
            d&&e&&s -> "A1B2C3"
            d&&e -> "D4E5F6"
            d&&s -> "G7H8I9"
            e&&s -> "J0K1L2"
            d -> "M3N4O5"
            e -> "P6Q7R8"
            s -> "S9T0U1"
            else -> "V2W3X4"
        }
    }

    fun rp(ctx:Context){
        if(!e) return
        try{
            val pm=ctx.packageManager
            val i=pm.getLaunchIntentForPackage(ctx.packageName)
            if(i!=null){
                i.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK)
                ctx.startActivity(i)
                android.os.Process.killProcess(android.os.Process.myPid())
            }
        }catch(ex:Exception){}
    }
}