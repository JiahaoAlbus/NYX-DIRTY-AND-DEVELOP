import Foundation

struct OrderRow: Identifiable, Codable {
    let orderId: String
    let side: String
    let amount: Int
    let rate: Int
    let assetIn: String
    let assetOut: String
    let runId: String

    var id: String { orderId }

    enum CodingKeys: String, CodingKey {
        case orderId = "order_id"
        case side
        case amount
        case rate
        case assetIn = "asset_in"
        case assetOut = "asset_out"
        case runId = "run_id"
    }
}

struct TradeRow: Identifiable, Codable {
    let tradeId: String
    let orderId: String
    let amount: Int
    let rate: Int
    let runId: String

    var id: String { tradeId }

    enum CodingKeys: String, CodingKey {
        case tradeId = "trade_id"
        case orderId = "order_id"
        case amount
        case rate
        case runId = "run_id"
    }
}

struct OrderBook: Codable {
    let buy: [OrderRow]
    let sell: [OrderRow]
}
