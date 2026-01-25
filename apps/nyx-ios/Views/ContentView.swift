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
    @Published var messages: [ChatMessage] = []
    @Published var listings: [ListingRow] = []
    @Published var purchases: [PurchaseRow] = []
    @Published var entertainmentItems: [EntertainmentItemRow] = []
    @Published var entertainmentEvents: [EntertainmentEventRow] = []
    @Published var walletAddress: String = "—"
    @Published var walletBalance: String = "0"
    @Published var evidence: EvidenceBundle?
    @Published var exportURL: URL?
    @Published var backendAvailable: Bool = false
    @Published var backendStatus: String = "Backend: unavailable"

    private let client = GatewayClient()
    private let walletStore = WalletStore()

    @MainActor
    func checkBackend() async {
        backendStatus = "Backend: checking..."
        let ok = await client.checkBackendAvailability(timeoutSeconds: 3.0)
        backendAvailable = ok
        backendStatus = ok ? "Backend: available" : "Backend: unavailable"
    }

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
            status = "Evidence ready. Testnet Beta. Provided by backend."
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
    func sendMessage(channel: String, body: String) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Sending message..."
        do {
            _ = try await client.sendMessage(seed: seedInt, runId: runId, payload: ["channel": channel, "message": body])
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshMessages(channel: channel)
            status = "Message sent. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshMessages(channel: String) async {
        do {
            messages = try await client.fetchMessages(channel: channel)
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func loadWallet() async {
        let trimmed = seed.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            status = "Seed required"
            return
        }
        walletStore.load(seed: trimmed)
        walletAddress = walletStore.address
        await refreshWalletBalance()
    }

    @MainActor
    func refreshWalletBalance() async {
        guard walletAddress != "—" else {
            walletBalance = "0"
            return
        }
        do {
            let balance = try await client.fetchWalletBalance(address: walletAddress)
            walletBalance = String(balance)
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func faucetWallet(amount: Int) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        if walletAddress == "—" {
            status = "Wallet address required"
            return
        }
        status = "Requesting testnet funds..."
        do {
            _ = try await client.walletFaucet(seed: seedInt, runId: runId, address: walletAddress, amount: amount)
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshWalletBalance()
            status = "Testnet funds credited. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func transferWallet(toAddress: String, amount: Int) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        if walletAddress == "—" {
            status = "Wallet address required"
            return
        }
        status = "Submitting transfer..."
        do {
            _ = try await client.walletTransfer(
                seed: seedInt,
                runId: runId,
                from: walletAddress,
                to: toAddress,
                amount: amount
            )
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshWalletBalance()
            status = "Transfer complete. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func publishListing(sku: String, title: String, price: Int) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Publishing listing..."
        do {
            _ = try await client.publishListing(seed: seedInt, runId: runId, payload: ["sku": sku, "title": title, "price": price])
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshListings()
            status = "Listing published. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func purchaseListing(listingId: String, qty: Int) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Submitting purchase..."
        do {
            _ = try await client.purchaseListing(seed: seedInt, runId: runId, listingId: listingId, qty: qty)
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshPurchases(listingId: listingId)
            status = "Purchase recorded. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshListings() async {
        do {
            listings = try await client.fetchListings()
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshPurchases(listingId: String) async {
        do {
            purchases = try await client.fetchPurchases(listingId: listingId)
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshEntertainmentItems() async {
        do {
            entertainmentItems = try await client.fetchEntertainmentItems()
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshEntertainmentEvents(itemId: String) async {
        do {
            entertainmentEvents = try await client.fetchEntertainmentEvents(itemId: itemId)
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func runEntertainmentStep(itemId: String, mode: String, step: Int) async {
        guard let seedInt = Int(seed) else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        status = "Executing step..."
        do {
            _ = try await client.runEntertainmentStep(seed: seedInt, runId: runId, itemId: itemId, mode: mode, step: step)
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshEntertainmentEvents(itemId: itemId)
            status = "Step recorded. Evidence ready."
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
        AppShell(model: model)
    }
}

struct AppShell: View {
    @ObservedObject var model: EvidenceViewModel

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("NYXPortal (Testnet)")
                    .font(.headline)
                Spacer()
                Text(model.backendStatus)
                    .font(.footnote)
                    .foregroundColor(model.backendAvailable ? .green : .secondary)
            }
            .padding()
            Divider()
            TabView {
                HomeView(model: model)
                    .tabItem { Label("Home", systemImage: "house") }
                WalletView(model: model)
                    .tabItem { Label("Wallet", systemImage: "creditcard") }
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
        .task {
            await model.checkBackend()
        }
    }
}
