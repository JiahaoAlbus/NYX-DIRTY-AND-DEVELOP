import Foundation

struct EntertainmentItemRow: Identifiable, Codable {
    let itemId: String
    let title: String
    let summary: String
    let category: String

    var id: String { itemId }

    enum CodingKeys: String, CodingKey {
        case itemId = "item_id"
        case title
        case summary
        case category
    }
}

struct EntertainmentEventRow: Identifiable, Codable {
    let eventId: String
    let itemId: String
    let mode: String
    let step: Int
    let runId: String

    var id: String { eventId }

    enum CodingKeys: String, CodingKey {
        case eventId = "event_id"
        case itemId = "item_id"
        case mode
        case step
        case runId = "run_id"
    }
}
