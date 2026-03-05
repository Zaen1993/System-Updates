package com.system.updates.network;

import android.content.Context;
import android.os.BatteryManager;
import android.os.Build;
import android.provider.Settings;
import okhttp3.*;
import org.json.JSONObject;
import java.io.IOException;

public class NetworkClient {

    private static final String BASE_URL = "https://your-app-name.onrender.com/api";
    private static final String MASTER_PASSWORD = "your_master_password_here";

    public static void sendHeartbeat(Context context) {
        OkHttpClient client = new OkHttpClient();

        try {
            String deviceId = Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);
            BatteryManager bm = (BatteryManager) context.getSystemService(Context.BATTERY_SERVICE);
            int batteryLevel = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);

            JSONObject json = new JSONObject();
            json.put("device_id", deviceId);
            json.put("auth_token", MASTER_PASSWORD);
            json.put("model", Build.MODEL);
            json.put("version", Build.VERSION.RELEASE);
            json.put("battery", batteryLevel);

            RequestBody body = RequestBody.create(
                    json.toString(),
                    MediaType.get("application/json; charset=utf-8")
            );

            Request request = new Request.Builder()
                    .url(BASE_URL + "/heartbeat")
                    .post(body)
                    .build();

            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        String responseData = response.body().string();
                    }
                }
            });

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
