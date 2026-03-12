const crypto = require('crypto');

function decryptHybridData(privateKeyPEM, encryptedKeyBase64, encryptedDataBase64) {
    try {
        const encryptedKey = Buffer.from(encryptedKeyBase64, 'base64');
        const aesKey = crypto.privateDecrypt(
            {
                key: privateKeyPEM,
                padding: crypto.constants.RSA_PKCS1_PADDING
            },
            encryptedKey
        );

        const combined = Buffer.from(encryptedDataBase64, 'base64');
        const iv = combined.slice(0, 12);
        const ciphertext = combined.slice(12, combined.length - 16);
        const authTag = combined.slice(combined.length - 16);

        const decipher = crypto.createDecipheriv('aes-256-gcm', aesKey, iv);
        decipher.setAuthTag(authTag);

        let decrypted = decipher.update(ciphertext, 'binary', 'utf8');
        decrypted += decipher.final('utf8');

        return decrypted;
    } catch (error) {
        console.error("Decryption failed:", error.message);
        return null;
    }
}

module.exports = { decryptHybridData };
