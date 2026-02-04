import CryptoKit
import Foundation
import Security

// MARK: - Wallet (v1) Models

struct WalletAssetV1: Codable {
    let asset_id: String
    let name: String?
}

struct WalletBalanceRowV1: Codable {
    let asset_id: String
    let balance: Int
}

struct WalletBalancesV1Response: Codable {
    let address: String
    let assets: [WalletAssetV1]
    let balances: [WalletBalanceRowV1]
}

struct WalletTransferRowV1: Codable, Identifiable {
    let transfer_id: String
    let from_address: String
    let to_address: String
    let asset_id: String
    let amount: Int
    let fee_total: Int
    let treasury_address: String
    let run_id: String
    let state_hash: String?
    let receipt_hashes: [String]
    let replay_ok: Bool

    var id: String { transfer_id }
}

struct WalletTransfersV1Response: Codable {
    let address: String
    let transfers: [WalletTransferRowV1]
    let limit: Int
    let offset: Int
}

struct WalletSignature: Codable {
    let message: String
    let signatureHex: String
}

struct WalletTransferV1Response: Codable {
    let runId: String
    let status: String
    let stateHash: String
    let receiptHashes: [String]
    let replayOk: Bool
    let fromAddress: String
    let toAddress: String
    let amount: Int
    let feeTotal: Int
    let treasuryAddress: String
    let fromBalance: Int
    let toBalance: Int
    let treasuryBalance: Int

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status
        case stateHash = "state_hash"
        case receiptHashes = "receipt_hashes"
        case replayOk = "replay_ok"
        case fromAddress = "from_address"
        case toAddress = "to_address"
        case amount
        case feeTotal = "fee_total"
        case treasuryAddress = "treasury_address"
        case fromBalance = "from_balance"
        case toBalance = "to_balance"
        case treasuryBalance = "treasury_balance"
    }
}

final class WalletStore: ObservableObject {
    @Published var address: String = "—"
    @Published var status: String = "No wallet loaded"

    private let keyTag = "nyx.wallet.seed.v1"

    func deriveAddress(seed: String) -> String {
        let digest = SHA256.hash(data: Data("nyx-wallet:\(seed)".utf8))
        let hex = digest.compactMap { String(format: "%02x", $0) }.joined()
        return "nyx-testnet-\(hex.prefix(16))"
    }

    func sign(message: String, seed: String) -> String {
        let keyData = SHA256.hash(data: Data("nyx-wallet-key:\(seed)".utf8))
        let key = SymmetricKey(data: Data(keyData))
        let signature = HMAC<SHA256>.authenticationCode(for: Data(message.utf8), using: key)
        return signature.map { String(format: "%02x", $0) }.joined()
    }

    func verify(message: String, signatureHex: String, seed: String) -> Bool {
        let expected = sign(message: message, seed: seed)
        return expected == signatureHex
    }

    func load(seed: String) {
        guard !seed.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            status = "Seed required"
            return
        }
        if let data = seed.data(using: .utf8) {
            _ = KeychainHelper.store(key: keyTag, data: data)
        }
        address = deriveAddress(seed: seed)
        status = "Wallet loaded (testnet)"
    }

    func restore() {
        if let data = KeychainHelper.load(key: keyTag),
           let seed = String(data: data, encoding: .utf8),
           !seed.isEmpty {
            address = deriveAddress(seed: seed)
            status = "Wallet restored (testnet)"
        }
    }
}

enum KeychainHelper {
    static func store(key: String, data: Data) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock,
        ]
        SecItemDelete(query as CFDictionary)
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }

    static func load(key: String) -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: kCFBooleanTrue as Any,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        if status == errSecSuccess {
            return item as? Data
        }
        return nil
    }
}
