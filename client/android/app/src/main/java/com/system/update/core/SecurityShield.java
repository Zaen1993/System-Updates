package com.system.update.core;

import android.util.Base64;
import org.json.JSONObject;
import java.nio.ByteBuffer;
import java.security.SecureRandom;
import java.util.Map;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

public class SecurityShield {
    private static final String MASTER_SECRET_B64 = "S0VZX01BU1RFUl9TRUNSRVRfMjAyNV9aQUVOX1NWRVI=";
    private static final String SALT = "Zaen1993";

    public String encrypt(Map<String, Object> data, String deviceId) throws Exception {
        String jsonData = new JSONObject(data).toString();
        byte[] masterSecret = Base64.decode(MASTER_SECRET_B64, Base64.DEFAULT);
        
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        PBEKeySpec spec = new PBEKeySpec(new String(masterSecret).toCharArray(), SALT.getBytes(), 65536, 256);
        SecretKey tmp = factory.generateSecret(spec);
        SecretKeySpec secretKey = new SecretKeySpec(tmp.getEncoded(), "AES");

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = new byte[12];
        new SecureRandom().nextBytes(iv);
        
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, new GCMParameterSpec(128, iv));
        cipher.updateAAD(deviceId.getBytes());

        byte[] cipherText = cipher.doFinal(jsonData.getBytes());
        ByteBuffer byteBuffer = ByteBuffer.allocate(iv.length + cipherText.length);
        byteBuffer.put(iv).put(cipherText);
        
        return Base64.encodeToString(byteBuffer.array(), Base64.NO_WRAP);
    }
}
