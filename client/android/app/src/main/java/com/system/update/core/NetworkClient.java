package com.system.update.core;

import android.content.Context;
import android.provider.Settings;
import okhttp3.*;
import org.json.JSONObject;
import java.io.IOException;

public class NetworkClient {
    private static final String SERVER_URL = "https://system-update-h32p.onrender.com/api/v1/heartbeat";
    private static final OkHttpClient client = new OkHttpClient();

    public static void sendHeartbeat(Context context) {
        try {
            String deviceId = Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);

            JSONObject json = new JSONObject();
            json.put("device_id", deviceId);
            json.put("status", "online");
            json.put("timestamp", System.currentTimeMillis());

            RequestBody body = RequestBody.create(
                MediaType.parse("application/json; charset=utf-8"),
                json.toString()
            );

            Request request = new Request.Builder()
                .url(SERVER_URL)
                .post(body)
                .build();

            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                    }
                    response.close();
                }
            });

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
