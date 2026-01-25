import SwiftUI

struct SolsticePalette {
    static let background = Color(red: 0.99, green: 0.98, blue: 0.96)
    static let banner = Color(red: 0.99, green: 0.93, blue: 0.75)
    static let accent = Color(red: 0.93, green: 0.74, blue: 0.2)
    static let card = Color(red: 1.0, green: 0.98, blue: 0.94)
}

struct PreviewBanner: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.footnote)
            .padding(10)
            .frame(maxWidth: .infinity)
            .background(SolsticePalette.banner)
            .cornerRadius(8)
    }
}

private extension View {
    func nyxInputStyle() -> some View {
        padding(8)
            .background(RoundedRectangle(cornerRadius: 8).stroke(.secondary))
    }
}

struct RunInputsView: View {
    @ObservedObject var model: EvidenceViewModel

    var body: some View {
        let seedBinding = Binding<Int>(
            get: { Int(model.seed) ?? 0 },
            set: { model.seed = String($0) }
        )
        VStack(alignment: .leading, spacing: 12) {
            TextField("Seed", value: seedBinding, format: .number)
            #if os(iOS)
                .keyboardType(.numberPad)
            #endif
                .nyxInputStyle()
            TextField("Run ID", text: $model.runId)
                .nyxInputStyle()
            Text(model.status)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
    }
}

struct HomeView: View {
    @ObservedObject var model: EvidenceViewModel

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. No external accounts. No live data.")
                Text("NYX Portal")
                    .font(.largeTitle)
                Text("Deterministic evidence flows only.")
                    .foregroundColor(.secondary)
                RunInputsView(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("World")
            .background(SolsticePalette.background)
        }
    }
}

struct WalletView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var transferTo = "receiver-001"
    @State private var transferAmount = 5
    @State private var faucetAmount = 50

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. Local wallet only. No external account linkage.")
                RunInputsView(model: model)
                Button("Load Wallet from Seed") {
                    Task {
                        await model.loadWallet()
                    }
                }
                .buttonStyle(.borderedProminent)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Address")
                        .font(.headline)
                    Text(model.walletAddress)
                        .font(.footnote)
                        .foregroundColor(.secondary)
                    Text("Balance")
                        .font(.headline)
                        .padding(.top, 6)
                    Text(model.walletBalance)
                        .font(.footnote)
                }
                Button("Refresh Balance") {
                    Task {
                        await model.refreshWalletBalance()
                    }
                }
                .buttonStyle(.bordered)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Testnet Faucet")
                        .font(.headline)
                    TextField("Amount", value: $faucetAmount, format: .number)
                    #if os(iOS)
                        .keyboardType(.numberPad)
                    #endif
                        .nyxInputStyle()
                    Button("Request Testnet Funds") {
                        Task {
                            await model.faucetWallet(amount: faucetAmount)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Transfer")
                        .font(.headline)
                    TextField("To Address", text: $transferTo)
                        .nyxInputStyle()
                    TextField("Amount", value: $transferAmount, format: .number)
                    #if os(iOS)
                        .keyboardType(.numberPad)
                    #endif
                        .nyxInputStyle()
                    Button("Send Transfer") {
                        Task {
                            await model.transferWallet(toAddress: transferTo, amount: transferAmount)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Wallet")
            .background(SolsticePalette.background)
        }
    }
}

struct ExchangeView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var side = "BUY"
    @State private var assetIn = "asset-a"
    @State private var assetOut = "asset-b"
    @State private var amount = 5
    @State private var price = 10
    @State private var cancelOrderId = ""

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. No live market data.")
                RunInputsView(model: model)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Wallet Context")
                        .font(.headline)
                    Text(model.walletAddress)
                        .font(.footnote)
                        .foregroundColor(.secondary)
                    Text("Balance")
                        .font(.footnote)
                    Text(model.walletBalance)
                        .font(.footnote)
                        .foregroundColor(.secondary)
                    Button("Refresh Wallet Balance") {
                        Task {
                            await model.refreshWalletBalance()
                        }
                    }
                    .buttonStyle(.bordered)
                }
                Picker("Side", selection: $side) {
                    Text("BUY").tag("BUY")
                    Text("SELL").tag("SELL")
                }
                .pickerStyle(.segmented)
                Picker("Asset In", selection: $assetIn) {
                    Text("asset-a").tag("asset-a")
                    Text("asset-b").tag("asset-b")
                }
                .pickerStyle(.segmented)
                Picker("Asset Out", selection: $assetOut) {
                    Text("asset-b").tag("asset-b")
                    Text("asset-c").tag("asset-c")
                }
                .pickerStyle(.segmented)
                TextField("Amount", value: $amount, format: .number)
                #if os(iOS)
                    .keyboardType(.numberPad)
                #endif
                    .nyxInputStyle()
                TextField("Price", value: $price, format: .number)
                #if os(iOS)
                    .keyboardType(.numberPad)
                #endif
                    .nyxInputStyle()
                Button("Place Order") {
                    Task {
                        await model.placeOrder(
                            payload: [
                                "side": side,
                                "asset_in": assetIn,
                                "asset_out": assetOut,
                                "amount": amount,
                                "price": price,
                            ]
                        )
                    }
                }
                .buttonStyle(.borderedProminent)

                TextField("Cancel Order ID", text: $cancelOrderId)
                    .nyxInputStyle()
                Button("Cancel Order") {
                    Task {
                        await model.cancelOrder(orderId: cancelOrderId)
                    }
                }
                .buttonStyle(.bordered)

                Button("Refresh Orderbook") {
                    Task {
                        await model.refreshOrderBook()
                        await model.refreshTrades()
                    }
                }
                .buttonStyle(.bordered)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Orderbook (Buy)")
                        .font(.headline)
                    ForEach(model.buyOrders.prefix(5)) { order in
                        Text("\(order.amount) @ \(order.price) \(order.assetIn)/\(order.assetOut)")
                            .font(.footnote)
                    }
                    Text("Orderbook (Sell)")
                        .font(.headline)
                        .padding(.top, 8)
                    ForEach(model.sellOrders.prefix(5)) { order in
                        Text("\(order.amount) @ \(order.price) \(order.assetIn)/\(order.assetOut)")
                            .font(.footnote)
                    }
                    Text("Trades")
                        .font(.headline)
                        .padding(.top, 8)
                    ForEach(model.trades.prefix(5)) { trade in
                        Text("\(trade.amount) @ \(trade.price)")
                            .font(.footnote)
                    }
                }
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Exchange")
            .background(SolsticePalette.background)
        }
    }
}

struct ChatView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var channel = "general"
    @State private var message = "Hello"

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. No external accounts or live chat history.")
                RunInputsView(model: model)
                TextField("Channel", text: $channel)
                    .nyxInputStyle()
                TextField("Message", text: $message)
                    .nyxInputStyle()
                Button("Send Message") {
                    Task {
                        await model.sendMessage(channel: channel, body: message)
                    }
                }
                .buttonStyle(.borderedProminent)
                Button("Refresh Messages") {
                    Task {
                        await model.refreshMessages(channel: channel)
                    }
                }
                .buttonStyle(.bordered)
                VStack(alignment: .leading, spacing: 8) {
                    Text("Recent Messages")
                        .font(.headline)
                    ForEach(model.messages.prefix(6)) { item in
                        Text("[\(item.channel)] \(item.body)")
                            .font(.footnote)
                    }
                }
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Chat")
            .background(SolsticePalette.background)
        }
    }
}

struct MarketplaceView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var sku = "sku-1"
    @State private var title = "Signal Pack"
    @State private var price = 10
    @State private var selectedListingId = ""
    @State private var quantity = 1

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. Listings are testnet-only.")
                RunInputsView(model: model)
                TextField("SKU", text: $sku)
                    .nyxInputStyle()
                TextField("Title", text: $title)
                    .nyxInputStyle()
                TextField("Price", value: $price, format: .number)
                #if os(iOS)
                    .keyboardType(.numberPad)
                #endif
                    .nyxInputStyle()
                Button("Publish Listing") {
                    Task {
                        await model.publishListing(sku: sku, title: title, price: price)
                    }
                }
                .buttonStyle(.borderedProminent)

                Button("Refresh Listings") {
                    Task {
                        await model.refreshListings()
                    }
                }
                .buttonStyle(.bordered)

                if !model.listings.isEmpty {
                    Picker("Listing", selection: $selectedListingId) {
                        ForEach(model.listings) { listing in
                            Text("\(listing.title) (\(listing.price))").tag(listing.listingId)
                        }
                    }
                    .pickerStyle(.menu)
                }
                TextField("Quantity", value: $quantity, format: .number)
                #if os(iOS)
                    .keyboardType(.numberPad)
                #endif
                    .nyxInputStyle()
                Button("Purchase Listing") {
                    if selectedListingId.isEmpty, let first = model.listings.first {
                        selectedListingId = first.listingId
                    }
                    Task {
                        await model.purchaseListing(listingId: selectedListingId, qty: quantity)
                    }
                }
                .buttonStyle(.borderedProminent)
                if !model.purchases.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Purchases")
                            .font(.headline)
                        ForEach(model.purchases.prefix(6)) { purchase in
                            Text("\(purchase.qty) from \(purchase.listingId)")
                                .font(.footnote)
                        }
                    }
                }
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Marketplace")
            .background(SolsticePalette.background)
        }
    }
}

struct EntertainmentView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var selectedItemId = ""
    @State private var mode = "pulse"
    @State private var step = 1

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. Deterministic steps.")
                RunInputsView(model: model)
                Button("Refresh Items") {
                    Task {
                        await model.refreshEntertainmentItems()
                    }
                }
                .buttonStyle(.bordered)

                if !model.entertainmentItems.isEmpty {
                    Picker("Item", selection: $selectedItemId) {
                        ForEach(model.entertainmentItems) { item in
                            Text(item.title).tag(item.itemId)
                        }
                    }
                    .pickerStyle(.menu)
                }

                Picker("Mode", selection: $mode) {
                    Text("Pulse").tag("pulse")
                    Text("Drift").tag("drift")
                    Text("Scan").tag("scan")
                }
                .pickerStyle(.segmented)
                TextField("Step", value: $step, format: .number)
                #if os(iOS)
                    .keyboardType(.numberPad)
                #endif
                    .nyxInputStyle()
                Button("Execute Step") {
                    Task {
                        if selectedItemId.isEmpty, let first = model.entertainmentItems.first {
                            selectedItemId = first.itemId
                        }
                        await model.runEntertainmentStep(itemId: selectedItemId, mode: mode, step: step)
                    }
                }
                .buttonStyle(.borderedProminent)
                if !model.entertainmentEvents.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recent Events")
                            .font(.headline)
                        ForEach(model.entertainmentEvents.prefix(6)) { event in
                            Text("\(event.itemId) • \(event.mode) • step \(event.step)")
                                .font(.footnote)
                        }
                    }
                }
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Entertainment")
            .background(SolsticePalette.background)
            .onAppear {
                Task {
                    await model.refreshEntertainmentItems()
                }
            }
        }
    }
}

struct TrustView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Beta. Evidence-first operations.")
                Text("Trust & Evidence")
                    .font(.title2)
                Text("Testnet Beta. No live data. Evidence is deterministic and replayable.")
                    .foregroundColor(.secondary)
                Spacer()
            }
            .padding()
            .navigationTitle("Trust")
            .background(SolsticePalette.background)
        }
    }
}

struct EvidenceSummary: View {
    @ObservedObject var model: EvidenceViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("state_hash: \(model.stateHash)")
                .font(.footnote)
            Text("receipt_hashes: \(model.receiptHashes.joined(separator: ", "))")
                .font(.footnote)
            Text("replay_ok: \(String(model.replayOk))")
                .font(.footnote)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(SolsticePalette.card)
        .cornerRadius(12)
    }
}

struct EvidenceInspectorView: View {
    @ObservedObject var model: EvidenceViewModel

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Evidence is rendered verbatim from the backend.")
                Button("Fetch Export Bundle") {
                    Task {
                        await model.fetchExport()
                    }
                }
                .buttonStyle(.bordered)

                if let url = model.exportURL {
                    ShareLink(item: url) {
                        Text("Share Evidence Bundle")
                    }
                }

                if let evidence = model.evidence {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("protocol_anchor")
                                .font(.headline)
                            Text(evidence.protocolAnchor.description)
                                .font(.footnote)

                            Text("inputs")
                                .font(.headline)
                            Text(evidence.inputs.description)
                                .font(.footnote)

                            Text("outputs")
                                .font(.headline)
                            Text(evidence.outputs.description)
                                .font(.footnote)

                            Text("stdout")
                                .font(.headline)
                            Text(evidence.stdout)
                                .font(.footnote)
                        }
                    }
                } else {
                    Text("No evidence loaded yet.")
                        .foregroundColor(.secondary)
                }
                Spacer()
            }
            .padding()
            .navigationTitle("Evidence")
            .background(SolsticePalette.background)
        }
    }
}
