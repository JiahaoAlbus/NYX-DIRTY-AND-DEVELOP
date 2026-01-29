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
    @Published var chatMessages: [ChatMessageV1] = []
    @Published var chatRooms: [ChatRoomV1] = []
    @Published var listings: [ListingRow] = []
    @Published var purchases: [PurchaseRow] = []
    @Published var entertainmentItems: [EntertainmentItemRow] = []
    @Published var entertainmentEvents: [EntertainmentEventRow] = []
    @Published var walletAddress: String = "—"
    @Published var walletBalance: String = "0"
    @Published var portalHandle: String = "portal-user"
    @Published var portalAccountId: String = ""
    @Published var portalStatus: String = "Not signed in"
    @Published var portalToken: String = ""
    @Published var activityReceipts: [PortalReceiptRow] = []
    @Published var backendUrl: String = GatewayClient.defaultBaseURLString()
    @Published var availableEndpoints: Set<String> = []
    @Published var capabilityNotes: String = ""
    @Published var evidence: EvidenceBundle?
    @Published var exportURL: URL?
    @Published var backendAvailable: Bool = false
    @Published var backendStatus: String = "Backend: unavailable"

    private let client = GatewayClient()
    private let walletStore = WalletStore()
    private let portalKeyStore = PortalKeyStore.shared

    @MainActor
    func applyBackendUrl() async {
        let trimmed = backendUrl.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: trimmed), !trimmed.isEmpty else {
            status = "Backend URL invalid"
            return
        }
        UserDefaults.standard.set(trimmed, forKey: "nyx_backend_url")
        client.setBaseURL(url)
        backendUrl = trimmed
        status = "Backend URL updated"
        await refreshBackendStatus()
    }

    @MainActor
    func createPortalAccount() async {
        let handle = portalHandle.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if handle.isEmpty {
            status = "Handle required"
            return
        }
        status = "Creating portal account..."
        do {
            let pubkey = portalKeyStore.publicKeyBase64()
            let account = try await client.createPortalAccount(handle: handle, pubkey: pubkey)
            portalAccountId = account.accountId
            portalStatus = "Account created"
            status = "Portal account ready"
        } catch {
            portalStatus = "Account creation failed"
            status = "Backend unavailable"
            backendStatus = "Backend: unavailable"
            backendAvailable = false
        }
    }

    @MainActor
    func signInPortal() async {
        let accountId = portalAccountId.trimmingCharacters(in: .whitespacesAndNewlines)
        if accountId.isEmpty {
            status = "Account ID required"
            return
        }
        status = "Signing in..."
        do {
            let challenge = try await client.requestPortalChallenge(accountId: accountId)
            let signature = portalKeyStore.sign(nonce: challenge.nonce)
            let token = try await client.verifyPortalChallenge(accountId: accountId, nonce: challenge.nonce, signature: signature)
            portalToken = token.accessToken
            portalStatus = "Signed in"
            status = "Portal session active"
        } catch {
            portalStatus = "Sign-in failed"
            status = "Backend unavailable"
            backendStatus = "Backend: unavailable"
            backendAvailable = false
        }
    }

    @MainActor
    func signOutPortal() async {
        if portalToken.isEmpty {
            portalStatus = "Not signed in"
            return
        }
        do {
            try await client.logoutPortal(token: portalToken)
        } catch {
            // Best-effort logout.
        }
        portalToken = ""
        portalStatus = "Signed out"
        status = "Portal session ended"
    }

    private func requirePortalToken() -> String? {
        if portalToken.isEmpty {
            status = "Sign in required"
            return nil
        }
        return portalToken
    }

    func hasEndpoint(_ entry: String) -> Bool {
        return availableEndpoints.contains(entry)
    }

    @MainActor
    func refreshPortalActivity() async {
        guard let token = requirePortalToken() else { return }
        do {
            activityReceipts = try await client.fetchPortalActivity(token: token, limit: 50)
        } catch {
            backendStatus = "Backend: unavailable"
            backendAvailable = false
            status = "Backend unavailable"
        }
    }

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
    func refreshChatRooms() async {
        guard let token = requirePortalToken() else { return }
        do {
            chatRooms = try await client.listChatRooms(token: token)
        } catch {
            backendStatus = "Backend: unavailable"
            backendAvailable = false
            status = "Backend unavailable"
        }
    }

    @MainActor
    func createChatRoom(name: String) async {
        guard let token = requirePortalToken() else { return }
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            status = "Room name required"
            return
        }
        status = "Creating room..."
        do {
            _ = try await client.createChatRoom(token: token, name: trimmed)
            await refreshChatRooms()
            status = "Room ready"
        } catch {
            backendStatus = "Backend: unavailable"
            backendAvailable = false
            status = "Backend unavailable"
        }
    }

    @MainActor
    func sendChatMessage(roomId: String, body: String) async {
        guard Int(seed) != nil else {
            status = "Seed must be an integer"
            return
        }
        if runId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            status = "Run ID required"
            return
        }
        guard let token = requirePortalToken() else { return }
        let trimmed = body.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            status = "Message required"
            return
        }
        status = "Sending message..."
        do {
            _ = try await client.sendChatMessage(token: token, roomId: roomId, body: trimmed)
            let bundle = try await client.fetchEvidence(runId: runId)
            evidence = bundle
            stateHash = bundle.stateHash
            receiptHashes = bundle.receiptHashes
            replayOk = bundle.replayOk
            await refreshChatMessages(roomId: roomId)
            status = "Message sent. Evidence ready."
        } catch {
            status = "Error: \(error)"
        }
    }

    @MainActor
    func refreshChatMessages(roomId: String) async {
        guard let token = requirePortalToken() else { return }
        do {
            chatMessages = try await client.listChatMessages(token: token, roomId: roomId)
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
        guard let token = requirePortalToken() else { return }
        status = "Requesting testnet funds..."
        do {
            _ = try await client.faucetV1(token: token, seed: seedInt, runId: runId, address: walletAddress, amount: amount)
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
        guard let token = requirePortalToken() else { return }
        status = "Submitting transfer..."
        do {
            _ = try await client.transferV1(
                token: token,
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
    @MainActor
    func refreshBackendStatus() async {
        do {
            let ok = try await client.checkHealth()
            backendAvailable = ok
            backendStatus = ok ? "Backend: available" : "Backend: unavailable"
            if ok {
                let caps = try await client.fetchCapabilities()
                availableEndpoints = Set(caps.endpoints)
                capabilityNotes = caps.notes ?? ""
            } else {
                availableEndpoints = []
                capabilityNotes = ""
            }
        } catch {
            backendStatus = "Backend: unavailable"
            backendAvailable = false
            availableEndpoints = []
            capabilityNotes = ""
        }
    }
}

struct AppShellHeader: View {
    let statusText: String
    let isAvailable: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("NYXPortal (Testnet)")
                    .font(.headline)
                Text("Evidence-first operations. No live mainnet data.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Spacer()
            Text(statusText)
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(isAvailable ? Color.green.opacity(0.15) : Color.orange.opacity(0.15))
                .cornerRadius(8)
        }
        .padding()
        .background(SolsticePalette.card)
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
    @StateObject private var backendSettings = BackendSettings()

    var body: some View {
        VStack(spacing: 0) {
            AppShellHeader(statusText: model.backendStatus, isAvailable: model.backendAvailable)
            if !model.backendAvailable {
                OfflineBanner {
                    Task {
                        await model.refreshBackendStatus()
                    }
                }
                .padding([.leading, .trailing, .bottom])
            }
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
                SettingsView(settings: backendSettings)
                    .tabItem { Label("Settings", systemImage: "gearshape") }
            }
            .accentColor(SolsticePalette.accent)
        }
        .task {
            await model.checkBackend()
        }
    }
}
