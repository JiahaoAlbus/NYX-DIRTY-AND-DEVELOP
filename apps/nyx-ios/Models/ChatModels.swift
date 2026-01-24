import Foundation

struct ChatMessage: Identifiable, Codable {
    let messageId: String
    let channel: String
    let body: String
    let runId: String

    var id: String { messageId }

    enum CodingKeys: String, CodingKey {
        case messageId = "message_id"
        case channel
        case body
        case runId = "run_id"
    }
}
