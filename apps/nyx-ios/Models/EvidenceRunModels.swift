import Foundation

struct EvidenceRunSummary: Codable, Identifiable {
    let runId: String
    let status: String?

    var id: String { runId }

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status
    }
}

struct EvidenceRunList: Codable {
    let runs: [EvidenceRunSummary]
}
