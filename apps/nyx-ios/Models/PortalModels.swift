import Foundation

struct GatewayCapabilities: Codable {
    let modules: [String]
    let endpoints: [String]
    let notes: String?
}

struct PortalAccount: Codable, Identifiable {
    let accountId: String
    let handle: String
    let pubkey: String
    let createdAt: Int
    let status: String

    var id: String { accountId }

    enum CodingKeys: String, CodingKey {
        case accountId = "account_id"
        case handle
        case pubkey
        case createdAt = "created_at"
        case status
    }
}

struct PortalChallenge: Codable {
    let nonce: String
    let expiresAt: Int

    enum CodingKeys: String, CodingKey {
        case nonce
        case expiresAt = "expires_at"
    }
}

struct PortalAuthToken: Codable {
    let accessToken: String
    let expiresAt: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case expiresAt = "expires_at"
    }
}

struct ChatRoomV1: Codable, Identifiable {
    let roomId: String
    let name: String
    let createdAt: Int
    let isPublic: Bool

    var id: String { roomId }

    enum CodingKeys: String, CodingKey {
        case roomId = "room_id"
        case name
        case createdAt = "created_at"
        case isPublic = "is_public"
    }
}

struct ChatMessageV1: Codable, Identifiable {
    let messageId: String
    let roomId: String
    let senderAccountId: String
    let body: String
    let seq: Int

    var id: String { messageId }

    enum CodingKeys: String, CodingKey {
        case messageId = "message_id"
        case roomId = "room_id"
        case senderAccountId = "sender_account_id"
        case body
        case seq
    }
}

struct ChatReceipt: Codable {
    let prevDigest: String
    let msgDigest: String
    let chainHead: String

    enum CodingKeys: String, CodingKey {
        case prevDigest = "prev_digest"
        case msgDigest = "msg_digest"
        case chainHead = "chain_head"
    }
}

struct ChatMessageResponse: Codable {
    let message: ChatMessageV1
    let receipt: ChatReceipt
}

struct PortalReceiptRow: Codable, Identifiable {
    let receiptId: String
    let module: String
    let action: String
    let stateHash: String
    let receiptHashes: [String]
    let replayOk: Bool
    let runId: String

    var id: String { receiptId }

    enum CodingKeys: String, CodingKey {
        case receiptId = "receipt_id"
        case module
        case action
        case stateHash = "state_hash"
        case receiptHashes = "receipt_hashes"
        case replayOk = "replay_ok"
        case runId = "run_id"
    }
}

struct FaucetV1Response: Codable {
    let runId: String
    let status: String
    let stateHash: String
    let receiptHashes: [String]
    let replayOk: Bool
    let address: String
    let balance: Int
    let feeTotal: Int
    let treasuryAddress: String

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status
        case stateHash = "state_hash"
        case receiptHashes = "receipt_hashes"
        case replayOk = "replay_ok"
        case address
        case balance
        case feeTotal = "fee_total"
        case treasuryAddress = "treasury_address"
    }
}
