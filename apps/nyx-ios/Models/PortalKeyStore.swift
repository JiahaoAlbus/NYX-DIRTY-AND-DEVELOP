import CryptoKit
import Foundation
import Security

final class PortalKeyStore {
    static let shared = PortalKeyStore()
    private let service = "nyx.portal.key"

    func loadOrCreateKey() -> Data {
        if let existing = readKey() {
            return existing
        }
        var keyData = Data(count: 32)
        let result = keyData.withUnsafeMutableBytes { bytes -> Int32 in
            guard let base = bytes.baseAddress else { return errSecParam }
            return SecRandomCopyBytes(kSecRandomDefault, 32, base)
        }
        if result != errSecSuccess {
            return Data("fallback-testnet-key".utf8).prefix(32)
        }
        storeKey(keyData)
        return keyData
    }

    func publicKeyBase64() -> String {
        let key = loadOrCreateKey()
        return key.base64EncodedString()
    }

    func sign(nonce: String) -> String {
        let key = SymmetricKey(data: loadOrCreateKey())
        let data = Data(nonce.utf8)
        let signature = HMAC<SHA256>.authenticationCode(for: data, using: key)
        return Data(signature).base64EncodedString()
    }

    private func readKey() -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecReturnData as String: true,
        ]
        var item: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        if status == errSecSuccess, let data = item as? Data {
            return data
        }
        return nil
    }

    private func storeKey(_ data: Data) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecValueData as String: data,
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
}
