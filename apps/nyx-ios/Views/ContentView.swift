import SwiftUI

final class EvidenceViewModel: ObservableObject {
    @Published var seed: String = "123"
    @Published var runId: String = "ios-demo"
    @Published var status: String = "Ready"
    @Published var stateHash: String = "—"
    @Published var receiptHashes: [String] = []
    @Published var replayOk: Bool = false
    @Published var buyOrders: [OrderRow] = []
    @Published var sellOrders: [OrderRow] = []
    @Published var trades: [TradeRow] = []
    @Published var evidence: EvidenceBundle?
    @Published var exportURL: URL?

    private let client = GatewayClient()

    @MainActor
    func run(module: String, action: String, payload: [String: Any]) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Running deterministic flow..."
        do {
            _ = try await client.run(
                seed: seedInt,
                runId: runId,
                module: module,
                action: action,
                payload: payload
            )
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            status = "Evidence ready. Testnet Alpha. Provided by backend."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func placeOrder(payload: [String: Any]) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Placing order..."
        do {
            _ = try await client.placeOrder(seed: seedInt, runId: runId, payload: payload)
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshOrderBook()
            await refreshTrades()
            status = "Order placed. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func cancelOrder(orderId: String) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Cancelling order..."
        do {
            _ = try await client.cancelOrder(seed: seedInt, runId: runId, orderId: orderId)
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshOrderBook()
            await refreshTrades()
            status = "Order cancelled. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshOrderBook() async {
        do {
            let book = try await client.fetchOrderBook()
            buyOrders = book.buy
            sellOrders = book.sell
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshTrades() async {
        do {
            trades = try await client.fetchTrades()
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func fetchExport() async {
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        do {
            let data = try await client.fetchExportZip(runId: runId)
            let url = FileManager.default.temporaryDirectory.appendingPathComponent("evidence-\(runId).zip")
            try data.write(to: url)
            exportURL = url
            status = "Export bundle ready"
        } catch {
            status = "Error: \(error)"
        }
    }
}

struct ContentView: View {
    @StateObject private var model = EvidenceViewModel()

    var body: some View {
        TabView {
            HomeView(model: model)
                .tabItem { Label("Home", systemImage: "house") }
            ExchangeView(model: model)
                .tabItem { Label("Exchange", systemImage: "arrow.left.arrow.right") }
            ChatView(model: model)
                .tabItem { Label("Chat", systemImage: "bubble.left") }
            MarketplaceView(model: model)
                .tabItem { Label("Market", systemImage: "bag") }
            EntertainmentView(model: model)
                .tabItem { Label("Play", systemImage: "sparkles") }
            TrustView()
                .tabItem { Label("Trust", systemImage: "shield") }
            EvidenceInspectorView(model: model)
                .tabItem { Label("Evidence", systemImage: "doc.plaintext") }
        }
        .accentColor(SolsticePalette.accent)
    }
}
