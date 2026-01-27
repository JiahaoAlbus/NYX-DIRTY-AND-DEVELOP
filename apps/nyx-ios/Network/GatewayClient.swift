import Foundation

struct RunResponse: Codable {
    let runId: String
    let status: String
    let replayOk: Bool?

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status
        case replayOk = "replay_ok"
    }
}

struct GatewayError: Error {
    let message: String
}

final class GatewayClient {
    private var baseURL: URL
    private let maxRetries = 0
    private var evidenceCache: [String: EvidenceBundle] = [:]
    private let session: URLSession

    init(baseURL: URL = GatewayClient.resolvedBaseURL()) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 5
        config.timeoutIntervalForResource = 5
        self.session = URLSession(configuration: config)
    }

    private func requestData(_ request: URLRequest) async throws -> Data {
        var attempts = 0
        var lastError: Error?
        while attempts <= maxRetries {
            do {
                let (data, response) = try await session.data(for: request)
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw GatewayError(message: "invalid response")
                }
                if httpResponse.statusCode >= 400 {
                    let errorText = String(data: data, encoding: .utf8) ?? "request failed"
                    throw GatewayError(message: errorText)
                }
                return data
            } catch {
                lastError = error
                attempts += 1
            }
        }
        throw lastError ?? GatewayError(message: "backend unavailable")
    }

    private static func resolvedBaseURL() -> URL {
        if let raw = UserDefaults.standard.string(forKey: "nyx_backend_url"),
           let url = URL(string: raw) {
            return url
        }
        return URL(string: "http://127.0.0.1:8091") ?? URL(string: "http://localhost:8091")!
    }

    static func defaultBaseURLString() -> String {
        return resolvedBaseURL().absoluteString
    }

    func setBaseURL(_ url: URL) {
        baseURL = url
    }

    func currentBaseURL() -> URL {
        return baseURL
    }

    func checkHealth() async throws -> Bool {
        let url = baseURL.appendingPathComponent("healthz")
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: Bool].self, from: data)
        return payload["ok"] == true
    }

    func fetchCapabilities() async throws -> GatewayCapabilities {
        let url = baseURL.appendingPathComponent("capabilities")
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        return try JSONDecoder().decode(GatewayCapabilities.self, from: data)
    }

    func run(seed: Int, runId: String, module: String, action: String, payload: [String: Any]) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("run")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "module": module,
            "action": action,
            "payload": payload,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])

        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func placeOrder(seed: Int, runId: String, payload: [String: Any]) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("exchange/place_order")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": payload,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func cancelOrder(seed: Int, runId: String, orderId: String) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("exchange/cancel_order")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": ["order_id": orderId],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func fetchOrderBook() async throws -> OrderBook {
        let url = baseURL.appendingPathComponent("exchange/orderbook")
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        return try JSONDecoder().decode(OrderBook.self, from: data)
    }

    func fetchTrades() async throws -> [TradeRow] {
        let url = baseURL.appendingPathComponent("exchange/trades")
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [TradeRow]].self, from: data)
        return payload["trades"] ?? []
    }

    func sendMessage(seed: Int, runId: String, payload: [String: Any]) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("chat/send")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": payload,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func fetchMessages(channel: String) async throws -> [ChatMessage] {
        var components = URLComponents(url: baseURL.appendingPathComponent("chat/messages"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "channel", value: channel)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [ChatMessage]].self, from: data)
        return payload["messages"] ?? []
    }

    func createPortalAccount(handle: String, pubkey: String) async throws -> PortalAccount {
        let url = baseURL.appendingPathComponent("portal/v1/accounts")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(
            withJSONObject: ["handle": handle, "pubkey": pubkey],
            options: [.sortedKeys]
        )
        let data = try await requestData(request)
        return try JSONDecoder().decode(PortalAccount.self, from: data)
    }

    func requestPortalChallenge(accountId: String) async throws -> PortalChallenge {
        let url = baseURL.appendingPathComponent("portal/v1/auth/challenge")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(
            withJSONObject: ["account_id": accountId],
            options: [.sortedKeys]
        )
        let data = try await requestData(request)
        return try JSONDecoder().decode(PortalChallenge.self, from: data)
    }

    func verifyPortalChallenge(accountId: String, nonce: String, signature: String) async throws -> PortalAuthToken {
        let url = baseURL.appendingPathComponent("portal/v1/auth/verify")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(
            withJSONObject: ["account_id": accountId, "nonce": nonce, "signature": signature],
            options: [.sortedKeys]
        )
        let data = try await requestData(request)
        return try JSONDecoder().decode(PortalAuthToken.self, from: data)
    }

    func logoutPortal(token: String) async throws {
        let url = baseURL.appendingPathComponent("portal/v1/auth/logout")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        _ = try await requestData(request)
    }

    func fetchPortalMe(token: String) async throws -> PortalAccount {
        let url = baseURL.appendingPathComponent("portal/v1/me")
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let data = try await requestData(request)
        return try JSONDecoder().decode(PortalAccount.self, from: data)
    }

    func fetchPortalActivity(token: String, limit: Int) async throws -> [PortalReceiptRow] {
        var components = URLComponents(url: baseURL.appendingPathComponent("portal/v1/activity"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "limit", value: String(limit))]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [PortalReceiptRow]].self, from: data)
        return payload["receipts"] ?? []
    }

    func createChatRoom(token: String, name: String) async throws -> ChatRoomV1 {
        let url = baseURL.appendingPathComponent("chat/v1/rooms")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["name": name], options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(ChatRoomV1.self, from: data)
    }

    func listChatRooms(token: String) async throws -> [ChatRoomV1] {
        let url = baseURL.appendingPathComponent("chat/v1/rooms")
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [ChatRoomV1]].self, from: data)
        return payload["rooms"] ?? []
    }

    func sendChatMessage(token: String, roomId: String, body: String) async throws -> ChatMessageResponse {
        let url = baseURL.appendingPathComponent("chat/v1/rooms/\(roomId)/messages")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["body": body], options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(ChatMessageResponse.self, from: data)
    }

    func listChatMessages(token: String, roomId: String) async throws -> [ChatMessageV1] {
        let url = baseURL.appendingPathComponent("chat/v1/rooms/\(roomId)/messages")
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [ChatMessageV1]].self, from: data)
        return payload["messages"] ?? []
    }

    func faucetV1(token: String, seed: Int, runId: String, address: String, amount: Int) async throws -> FaucetV1Response {
        let url = baseURL.appendingPathComponent("wallet/v1/faucet")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": ["address": address, "amount": amount, "token": "NYXT"],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(FaucetV1Response.self, from: data)
    }

    func transferV1(token: String, seed: Int, runId: String, from: String, to: String, amount: Int) async throws -> WalletTransferV1Response {
        let url = baseURL.appendingPathComponent("wallet/v1/transfer")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": ["from_address": from, "to_address": to, "amount": amount],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(WalletTransferV1Response.self, from: data)
    }

    func publishListing(seed: Int, runId: String, payload: [String: Any]) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("marketplace/listing")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": payload,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func purchaseListing(seed: Int, runId: String, listingId: String, qty: Int) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("marketplace/purchase")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": ["listing_id": listingId, "qty": qty],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func fetchListings() async throws -> [ListingRow] {
        let url = baseURL.appendingPathComponent("marketplace/listings")
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [ListingRow]].self, from: data)
        return payload["listings"] ?? []
    }

    func fetchPurchases(listingId: String) async throws -> [PurchaseRow] {
        var components = URLComponents(url: baseURL.appendingPathComponent("marketplace/purchases"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "listing_id", value: listingId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [PurchaseRow]].self, from: data)
        return payload["purchases"] ?? []
    }

    func fetchEntertainmentItems() async throws -> [EntertainmentItemRow] {
        let url = baseURL.appendingPathComponent("entertainment/items")
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [EntertainmentItemRow]].self, from: data)
        return payload["items"] ?? []
    }

    func fetchEntertainmentEvents(itemId: String) async throws -> [EntertainmentEventRow] {
        var components = URLComponents(url: baseURL.appendingPathComponent("entertainment/events"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "item_id", value: itemId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: [EntertainmentEventRow]].self, from: data)
        return payload["events"] ?? []
    }

    func fetchWalletBalance(address: String) async throws -> Int {
        var components = URLComponents(url: baseURL.appendingPathComponent("wallet/balance"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "address", value: address)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let payload = try JSONDecoder().decode([String: Int].self, from: data)
        return payload["balance"] ?? 0
    }

    func walletFaucet(seed: Int, runId: String, address: String, amount: Int) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("wallet/faucet")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": ["address": address, "amount": amount],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func walletTransfer(seed: Int, runId: String, from: String, to: String, amount: Int) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("wallet/transfer")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": [
                "from_address": from,
                "to_address": to,
                "amount": amount,
            ],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func runEntertainmentStep(seed: Int, runId: String, itemId: String, mode: String, step: Int) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("entertainment/step")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "payload": ["item_id": itemId, "mode": mode, "step": step],
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func fetchEvidence(runId: String) async throws -> EvidenceBundle {
        if let cached = evidenceCache[runId] {
            return cached
        }
        var components = URLComponents(url: baseURL.appendingPathComponent("evidence"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "run_id", value: runId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let bundle = try JSONDecoder().decode(EvidenceBundle.self, from: data)
        evidenceCache[runId] = bundle
        return bundle
    }

    func fetchExportZip(runId: String) async throws -> Data {
        var components = URLComponents(url: baseURL.appendingPathComponent("export.zip"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "run_id", value: runId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        return try await requestData(request)
    }
}
