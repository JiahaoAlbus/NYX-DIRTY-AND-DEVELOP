import SwiftUI

// MARK: - Home View (Capability-driven)
struct NYXHomeView: View {
    @ObservedObject var settings: BackendSettings
    @Binding var selectedTab: Int
    @State private var backendOk: Bool = false
    @State private var statusText: String = "Backend: unknown"
    @State private var showWeb2Guard: Bool = false
    private let client = GatewayClient()
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("NYX Portal")
                            .font(.largeTitle)
                            .fontWeight(.black)
                        Text("Testnet • Mainnet-equivalent flows • Evidence for every mutation")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            Text(statusText)
                                .font(.footnote)
                                .foregroundColor(backendOk ? .green : .secondary)
                            Spacer()
                            Button("Refresh") {
                                Task { await refreshStatus() }
                            }
                            .buttonStyle(.bordered)
                        }

                        if let session = settings.session {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("@\(session.handle)")
                                    .font(.headline)
                                Text(session.account_id)
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                                    .textSelection(.enabled)
                            }
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(16)

                    VStack(alignment: .leading, spacing: 12) {
                        Text("Modules")
                            .font(.headline)
                        ModuleButton(icon: "wallet.pass.fill", title: "Wallet", subtitle: "Native balances • faucet • send", color: .yellow) {
                            selectedTab = 1
                        }
                        ModuleButton(icon: "arrow.left.arrow.right.circle.fill", title: "Trade", subtitle: "Web module (shared session)", color: .green) {
                            selectedTab = 2
                        }
                        ModuleButton(icon: "bubble.left.and.bubble.right.fill", title: "Chat", subtitle: "Web module (E2EE)", color: .blue) {
                            selectedTab = 3
                        }
                        ModuleButton(icon: "bag.fill", title: "Store", subtitle: "Web module (purchase receipts)", color: .orange) {
                            selectedTab = 4
                        }
                        ModuleButton(icon: "lock.shield.fill", title: "Web2 Guard", subtitle: "Allowlisted Web2 access", color: .purple) {
                            showWeb2Guard = true
                        }
                        ModuleButton(icon: "checkmark.seal.fill", title: "Evidence", subtitle: "Replay verify • proof export", color: .purple) {
                            selectedTab = 5
                        }
                    }
                }
                .padding()
                .padding(.bottom, 90)
            }
            .navigationTitle("Home")
        }
        .task {
            await refreshStatus()
        }
        .sheet(isPresented: $showWeb2Guard) {
            WebPortalView(settings: settings, initialScreen: "web2_access")
        }
    }

    @MainActor
    private func refreshStatus() async {
        guard let url = settings.resolvedURL() else {
            backendOk = false
            statusText = "Backend: invalid URL"
            return
        }
        client.setBaseURL(url)
        do {
            let ok = try await client.checkHealth()
            backendOk = ok
            statusText = ok ? "Backend: available" : "Backend: unavailable"
        } catch {
            backendOk = false
            statusText = "Backend: unavailable"
        }
    }
}

// MARK: - Wallet View (Native, no fake UI)
struct NYXWalletView: View {
    @ObservedObject var settings: BackendSettings
    @State private var assets: [WalletAssetV1] = []
    @State private var balances: [WalletBalanceRowV1] = []
    @State private var transfers: [WalletTransferRowV1] = []
    @State private var status: String = ""
    @State private var loading: Bool = false
    @State private var showFaucet: Bool = false
    @State private var showSend: Bool = false
    @State private var faucetAmount: String = "1000"
    @State private var faucetAsset: String = "NYXT"
    @State private var sendTo: String = ""
    @State private var sendAmount: String = ""
    @State private var sendAsset: String = "NYXT"
    @State private var transfersOffset: Int = 0
    @State private var lastReceipt: String = ""
    private let transfersPageSize: Int = 25
    private let client = GatewayClient()

    private var accountId: String { settings.session?.account_id ?? "" }
    private var token: String { settings.session?.access_token ?? "" }

    var body: some View {
        NavigationStack {
            VStack(spacing: 14) {
                if accountId.isEmpty || token.isEmpty {
                    Text("Sign in required.")
                        .foregroundColor(.secondary)
                } else {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Address")
                                .font(.headline)
                            Spacer()
                            Button("Copy") {
                                UIPasteboard.general.string = accountId
                            }
                            .buttonStyle(.bordered)
                        }
                        Text(accountId)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                            .textSelection(.enabled)
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(16)

                    HStack(spacing: 12) {
                        Button("Faucet") { showFaucet = true }
                            .buttonStyle(.borderedProminent)
                        Button("Send") { showSend = true }
                            .buttonStyle(.bordered)
                        Button("Refresh") { Task { await refreshAll(resetTransfers: true) } }
                            .buttonStyle(.bordered)
                    }

                    if loading {
                        ProgressView()
                    }
                    if !status.isEmpty {
                        Text(status)
                            .font(.footnote)
                            .foregroundColor(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    List {
                        Section(header: Text("Assets")) {
                            ForEach(assets, id: \.asset_id) { asset in
                                let bal = balances.first(where: { $0.asset_id == asset.asset_id })?.balance ?? 0
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(asset.asset_id)
                                            .fontWeight(.bold)
                                        if let name = asset.name {
                                            Text(name)
                                                .font(.caption2)
                                                .foregroundColor(.secondary)
                                        }
                                    }
                                    Spacer()
                                    Text("\(bal)")
                                        .font(.system(.body, design: .monospaced))
                                }
                            }
                        }

                        Section(header: Text("Transfers")) {
                            if transfers.isEmpty {
                                Text("No transfers yet.")
                                    .foregroundColor(.secondary)
                            } else {
                                ForEach(transfers) { t in
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            Text("\(t.amount) \(t.asset_id)")
                                                .fontWeight(.bold)
                                            Spacer()
                                            Text("fee \(t.fee_total)")
                                                .font(.caption2)
                                                .foregroundColor(.secondary)
                                        }
                                        Text("run_id: \(t.run_id)")
                                            .font(.caption2)
                                            .foregroundColor(.secondary)
                                            .textSelection(.enabled)
                                    }
                                }
                                Button("Load more") {
                                    Task { await loadTransfers(nextPage: true) }
                                }
                            }
                        }
                    }
                    .listStyle(.insetGrouped)

                    if !lastReceipt.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Last Receipt")
                                .font(.headline)
                            Text(lastReceipt)
                                .font(.caption2)
                                .foregroundColor(.secondary)
                                .textSelection(.enabled)
                        }
                        .padding()
                        .background(.ultraThinMaterial)
                        .cornerRadius(16)
                    }
                }
            }
            .padding(.horizontal)
            .padding(.top, 10)
            .navigationTitle("Wallet")
        }
        .task {
            await refreshAll(resetTransfers: true)
        }
        .sheet(isPresented: $showFaucet) {
            NavigationStack {
                Form {
                    Picker("Asset", selection: $faucetAsset) {
                        ForEach(assets.map(\.asset_id), id: \.self) { assetId in
                            Text(assetId).tag(assetId)
                        }
                    }
                    TextField("Amount", text: $faucetAmount)
                        .keyboardType(.numberPad)
                    Button("Claim Faucet") {
                        Task { await claimFaucet() }
                    }
                    .disabled(loading)
                }
                .navigationTitle("Faucet")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") { showFaucet = false }
                    }
                }
            }
        }
        .sheet(isPresented: $showSend) {
            NavigationStack {
                Form {
                    Picker("Asset", selection: $sendAsset) {
                        ForEach(assets.map(\.asset_id), id: \.self) { assetId in
                            Text(assetId).tag(assetId)
                        }
                    }
                    TextField("To Address", text: $sendTo)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled(true)
                    TextField("Amount", text: $sendAmount)
                        .keyboardType(.numberPad)
                    Button("Send") {
                        Task { await sendTransfer() }
                    }
                    .disabled(loading)
                }
                .navigationTitle("Send")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") { showSend = false }
                    }
                }
            }
        }
    }

    @MainActor
    private func refreshAll(resetTransfers: Bool) async {
        guard let url = settings.resolvedURL(), !accountId.isEmpty, !token.isEmpty else { return }
        loading = true
        status = ""
        client.setBaseURL(url)
        do {
            async let balancesResp = client.fetchWalletBalancesV1(token: token, address: accountId)
            let b = try await balancesResp
            assets = b.assets
            balances = b.balances
            if resetTransfers {
                transfersOffset = 0
                transfers = []
            }
            await loadTransfers(nextPage: false)
        } catch {
            status = "Load failed: \(String(describing: error))"
        }
        loading = false
    }

    @MainActor
    private func loadTransfers(nextPage: Bool) async {
        guard let url = settings.resolvedURL(), !accountId.isEmpty, !token.isEmpty else { return }
        client.setBaseURL(url)
        if nextPage {
            transfersOffset += transfersPageSize
        }
        do {
            let resp = try await client.fetchWalletTransfersV1(
                token: token,
                address: accountId,
                limit: transfersPageSize,
                offset: transfersOffset
            )
            if nextPage {
                transfers.append(contentsOf: resp.transfers)
            } else {
                transfers = resp.transfers
            }
        } catch {
            status = "Transfers load failed: \(String(describing: error))"
        }
    }

    private func parseSeedValue() -> Int? {
        let trimmed = settings.seed.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let value = Int(trimmed), value >= 0 else { return nil }
        return value
    }

    private func allocateRunId(action: String) -> String {
        let base = settings.runIdBase.trimmingCharacters(in: .whitespacesAndNewlines)
        let safeBase = base.isEmpty ? "ios-run" : base
        let safeAction = action.replacingOccurrences(of: "[^A-Za-z0-9_-]", with: "_", options: .regularExpression)
        let key = "nyx_run_counter_\(safeBase)"
        let current = UserDefaults.standard.integer(forKey: key)
        let next = current + 1
        UserDefaults.standard.set(next, forKey: key)
        return "\(safeBase)-\(safeAction)-\(next)"
    }

    @MainActor
    private func claimFaucet() async {
        guard let url = settings.resolvedURL(), !accountId.isEmpty, !token.isEmpty else { return }
        guard let seedValue = parseSeedValue() else {
            status = "Seed must be a non-negative integer"
            return
        }
        guard let amount = Int(faucetAmount.trimmingCharacters(in: .whitespacesAndNewlines)), amount > 0 else {
            status = "Amount must be a positive integer"
            return
        }
        loading = true
        status = ""
        client.setBaseURL(url)
        do {
            let runId = allocateRunId(action: "faucet")
            let result = try await client.faucetV1(token: token, seed: seedValue, runId: runId, address: accountId, amount: amount, assetId: faucetAsset)
            lastReceipt = "run_id=\(result.runId) state_hash=\(result.stateHash) fee_total=\(result.feeTotal) treasury=\(result.treasuryAddress)"
            showFaucet = false
            await refreshAll(resetTransfers: true)
        } catch {
            status = "Faucet failed: \(String(describing: error))"
        }
        loading = false
    }

    @MainActor
    private func sendTransfer() async {
        guard let url = settings.resolvedURL(), !accountId.isEmpty, !token.isEmpty else { return }
        guard let seedValue = parseSeedValue() else {
            status = "Seed must be a non-negative integer"
            return
        }
        let to = sendTo.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !to.isEmpty else {
            status = "To address required"
            return
        }
        guard let amount = Int(sendAmount.trimmingCharacters(in: .whitespacesAndNewlines)), amount > 0 else {
            status = "Amount must be a positive integer"
            return
        }
        loading = true
        status = ""
        client.setBaseURL(url)
        do {
            let runId = allocateRunId(action: "transfer")
            let result = try await client.transferV1(token: token, seed: seedValue, runId: runId, from: accountId, to: to, amount: amount, assetId: sendAsset)
            lastReceipt = "run_id=\(result.runId) state_hash=\(result.stateHash) fee_total=\(result.feeTotal) treasury=\(result.treasuryAddress)"
            showSend = false
            sendTo = ""
            sendAmount = ""
            await refreshAll(resetTransfers: true)
        } catch {
            status = "Send failed: \(String(describing: error))"
        }
        loading = false
    }
}

// MARK: - Subviews
struct ShortcutIcon: View {
    let icon: String
    let label: String
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title3)
                .frame(width: 50, height: 50)
                .background(.ultraThinMaterial)
                .cornerRadius(15)
            Text(label)
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(.secondary)
        }
    }
}

struct ModuleRow: View {
    let icon: String
    let title: String
    let desc: String
    let color: Color
    var body: some View {
        HStack(spacing: 15) {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 44, height: 44)
                .background(color.opacity(0.1))
                .cornerRadius(12)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 14, weight: .bold))
                Text(desc).font(.system(size: 10)).foregroundColor(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.caption).foregroundColor(.secondary)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(20)
        .padding(.horizontal)
    }
}

struct ModuleButton: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .frame(width: 36, height: 36)
                    .background(color.opacity(0.12))
                    .cornerRadius(10)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.headline)
                    Text(subtitle).font(.caption).foregroundColor(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right").font(.caption).foregroundColor(.secondary)
            }
            .padding()
            .background(.ultraThinMaterial)
            .cornerRadius(16)
        }
        .buttonStyle(.plain)
    }
}

struct WalletActionBtn: View {
    let icon: String
    let label: String
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.headline)
                .foregroundColor(.black)
                .frame(width: 44, height: 44)
                .background(Color.yellow)
                .cornerRadius(22)
            Text(label).font(.caption).fontWeight(.bold).foregroundColor(.yellow)
        }
    }
}

struct NYXExchangeView: View { 
    var body: some View { 
        VStack {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 50))
                .foregroundColor(.green)
            Text("NYX Exchange")
                .font(.title)
                .fontWeight(.bold)
            Text("High-performance deterministic trading engine.")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    } 
}
struct NYXChatView: View { 
    var body: some View { 
        VStack {
            Image(systemName: "bubble.left.and.bubble.right.fill")
                .font(.system(size: 50))
                .foregroundColor(.blue)
            Text("NYX Chat")
                .font(.title)
                .fontWeight(.bold)
            Text("P2P E2EE encrypted messaging service.")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    } 
}
struct NYXStoreView: View { 
    var body: some View { 
        VStack {
            Image(systemName: "bag.fill")
                .font(.system(size: 50))
                .foregroundColor(.orange)
            Text("NYX Store")
                .font(.title)
                .fontWeight(.bold)
            Text("Deterministic marketplace for digital assets.")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    } 
}
