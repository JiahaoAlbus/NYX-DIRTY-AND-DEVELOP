import SwiftUI

// MARK: - Home View (Binance Style)
struct NYXHomeView: View {
    @ObservedObject var settings: BackendSettings
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    HStack {
                        VStack(alignment: .leading) {
                            Text("NYX Portal")
                                .font(.largeTitle)
                                .fontWeight(.black)
                            Text("Testnet Ecosystem")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        Image(systemName: "diamond.fill")
                            .font(.system(size: 30))
                            .foregroundColor(.yellow)
                    }
                    .padding(.horizontal)
                    
                    // Banner
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Secure Your Future")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        Text("Deterministic Web3 Infrastructure")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(.secondary)
                        
                        Button(action: {}) {
                            Text("Claim Airdrop")
                                .font(.caption)
                                .fontWeight(.bold)
                                .padding(.horizontal, 20)
                                .padding(.vertical, 8)
                                .background(Color.accentColor)
                                .foregroundColor(.black)
                                .cornerRadius(10)
                        }
                        .padding(.top, 10)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(25)
                    .background(LinearGradient(colors: [.yellow, .orange], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .cornerRadius(25)
                    .padding(.horizontal)
                    
                    // Quick Actions
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())]) {
                        ShortcutIcon(icon: "drop.fill", label: "Faucet")
                        ShortcutIcon(icon: "banknote.fill", label: "Fiat")
                        ShortcutIcon(icon: "gift.fill", label: "Airdrop")
                        ShortcutIcon(icon: "ellipsis.circle.fill", label: "More")
                    }
                    .padding(.horizontal)
                    
                    // Modules
                    VStack(alignment: .leading, spacing: 15) {
                        Text("Core Modules")
                            .font(.headline)
                            .padding(.horizontal)
                        
                        ModuleRow(icon: "wallet.pass.fill", title: "Web3 Wallet", desc: "MetaMask-style assets", color: .yellow)
                        ModuleRow(icon: "arrow.left.arrow.right", title: "Exchange", desc: "Binance-style trading", color: .green)
                        ModuleRow(icon: "bubble.left.and.bubble.right.fill", title: "Chat", desc: "Instagram-style social", color: .blue)
                        ModuleRow(icon: "bag.fill", title: "Store", desc: "Taobao-style marketplace", color: .orange)
                    }
                }
                .padding(.bottom, 100)
            }
            .navigationBarHidden(true)
        }
    }
}

// MARK: - Wallet View (MetaMask Style)
struct NYXWalletView: View {
    @ObservedObject var settings: BackendSettings
    @State private var balance: Int = 0
    @State private var address: String = "0x0Aa313...CBc"
    @State private var isRefreshing = false
    
    func refreshBalance() async {
        isRefreshing = true
        guard let url = URL(string: settings.baseURL)?.appendingPathComponent("wallet/balance") else { return }
        var components = URLComponents(url: url, resolvingAgainstBaseURL: true)
        components?.queryItems = [URLQueryItem(name: "address", value: address)]
        
        guard let finalURL = components?.url else { return }
        
        do {
            let (data, _) = try await URLSession.shared.data(from: finalURL)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let bal = json["balance"] as? Int {
                self.balance = bal
            }
        } catch {
            print("Failed to fetch balance: \(error)")
        }
        isRefreshing = false
    }

    func requestFaucet() async {
        guard let account = settings.session?.account_id else { return }
        let client = GatewayClient(baseURL: URL(string: settings.baseURL)!)
        do {
            _ = try await client.faucetV1(
                token: settings.session?.access_token ?? "",
                seed: Int.random(in: 1...1000000),
                runId: "faucet-\(Date().timeIntervalSince1970)",
                address: account,
                amount: 1000000000 // 1000 NYXT
            )
            await refreshBalance()
        } catch {
            print("Faucet failed: \(error)")
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Account Card
                VStack(spacing: 15) {
                    Circle()
                        .fill(LinearGradient(colors: [.yellow, .orange], startPoint: .top, endPoint: .bottom))
                        .frame(width: 60, height: 60)
                        .overlay(Text("N").fontWeight(.bold).foregroundColor(.black))
                    
                    Text("@NYXUser")
                        .font(.headline)
                    
                    HStack {
                        Text(address)
                            .font(.system(.caption, design: .monospaced))
                        Button(action: {
                            UIPasteboard.general.string = address
                        }) {
                            Image(systemName: "doc.on.doc").font(.caption2)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(.ultraThinMaterial)
                    .cornerRadius(15)
                }
                .padding(.vertical, 30)
                .frame(maxWidth: .infinity)
                .background(Color.yellow.opacity(0.1))
                
                // Balance
                VStack(spacing: 8) {
                    Text("\(balance) NYXT")
                        .font(.system(size: 40, weight: .black, design: .rounded))
                    Text("≈ $\(Double(balance) / 1_000_000_000.0, specifier: "%.2f")")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 20)
                
                // Actions
                HStack(spacing: 30) {
                    WalletActionBtn(icon: "plus", label: "Buy")
                    WalletActionBtn(icon: "arrow.up", label: "Send")
                    WalletActionBtn(icon: "arrow.left.arrow.right", label: "Swap")
                    Button(action: {
                        Task { await requestFaucet() }
                    }) {
                        WalletActionBtn(icon: "drop", label: "Faucet")
                    }
                }
                .padding(.bottom, 30)
                
                // Assets
                List {
                    Section(header: Text("Assets")) {
                        HStack {
                            Circle().fill(.yellow).frame(width: 32)
                            VStack(alignment: .leading) {
                                Text("NYXT").fontWeight(.bold)
                                Text("NYX Testnet Token").font(.caption2).foregroundColor(.secondary)
                            }
                            Spacer()
                            Text("\(balance)").fontWeight(.bold)
                        }
                    }
                }
                .listStyle(InsetGroupedListStyle())
                .refreshable {
                    await refreshBalance()
                }
            }
            .navigationTitle("Wallet")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task { await refreshBalance() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                            .rotationEffect(.degrees(isRefreshing ? 360 : 0))
                            .animation(isRefreshing ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: isRefreshing)
                    }
                }
            }
        }
        .task {
            await refreshBalance()
        }
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
