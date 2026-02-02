import Foundation

struct ListingRow: Identifiable, Codable {
    let listingId: String
    let sku: String
    let title: String
    let rate: Int
    let runId: String

    var id: String { listingId }

    enum CodingKeys: String, CodingKey {
        case listingId = "listing_id"
        case sku
        case title
        case rate
        case runId = "run_id"
    }
}

struct PurchaseRow: Identifiable, Codable {
    let purchaseId: String
    let listingId: String
    let qty: Int
    let runId: String

    var id: String { purchaseId }

    enum CodingKeys: String, CodingKey {
        case purchaseId = "purchase_id"
        case listingId = "listing_id"
        case qty
        case runId = "run_id"
    }
}
