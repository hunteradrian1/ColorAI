const FingerprintJS = require("@fingerprintjs/fingerprintjs");
const CryptoJS = require("crypto-js");
const forge = require("node-forge");

const clientKey = process.env.REACT_APP_CLIENT_KEY;
const isDevelopment = process.env.NODE_ENV === 'development';

/**
 * Generates a unique fingerprint for the given device.
 * Uses the FingerprintJS library.
 * @returns {Promise<string>} unique fingerprint
 */
async function generateFingerprint(): Promise<string> {
  const fp = await FingerprintJS.load();
  const result = await fp.get();
  return result.visitorId;
}

/**
 * One-way encrypts input data.
 * Using CryptoJS to create an irreversible hash (MD5).
 * @param {string} data
 * @returns {string} encrypted data
 */
function irreversibleEncrypt(data: string): string {
  return CryptoJS.MD5(data).toString();
}

/**
 * Two-way encrypts input data using a public key.
 * Using node-forge to create an RSA-OAEP encrypted string.
 * @param {string} data
 * @param {string} key
 * @returns {string} encrypted data
 */
function reversibleEncrypt(data: string, key: string): string {
  if (!key) {
    throw new Error("Client key is not configured. Please set REACT_APP_CLIENT_KEY environment variable.");
  }
  
  try {
    const encryptor = forge.pki.publicKeyFromPem(key);
    const encrypted = encryptor.encrypt(data, "RSA-OAEP");
    return forge.util.encode64(encrypted);
  } catch (error) {
    throw new Error(`Failed to encrypt data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Generates a unique API key using unique device fingerprint.
 * The fingerprint is encrypted using irreversible encryption for security.
 * In development mode, uses a simplified approach without encryption.
 * @returns {Promise<{ key: string, signature: string }>} encrypted key and signature
 */
export const generateAPIKey = (): Promise<{
  key: string;
  signature: string;
}> => {
  return generateFingerprint().then((fingerprint) => {
    const encrypted1 = irreversibleEncrypt(fingerprint);
    
    // In development mode, skip encryption if no client key is provided
    if (isDevelopment && !clientKey) {
      console.warn("Development mode: Using simplified API key generation without encryption");
      return { key: encrypted1, signature: encrypted1 }; // Use the same value for both
    }
    
    if (!clientKey) {
      return Promise.reject(new Error("Client key is not configured. Please set REACT_APP_CLIENT_KEY environment variable."));
    }
    
    const encrypted2 = reversibleEncrypt(encrypted1, clientKey);
    return { key: encrypted1, signature: encrypted2 };
  });
};
