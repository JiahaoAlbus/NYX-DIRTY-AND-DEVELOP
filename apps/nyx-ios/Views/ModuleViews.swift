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

struct RunInputsView: View {
    @ObservedObject var model: EvidenceViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            TextField("Seed", text: $model.seed)
                .keyboardType(.numberPad)
                .textFieldStyle(.roundedBorder)
            TextField("Run ID", text: $model.runId)
                .textFieldStyle(.roundedBorder)
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
                PreviewBanner(text: "Testnet Alpha. Preview only. No accounts. No live data.")
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

struct ExchangeView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var assetIn = "asset-a"
    @State private var assetOut = "asset-b"
    @State private var amount = "5"
    @State private var minOut = "3"

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Alpha. No live market data.")
                RunInputsView(model: model)
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
                TextField("Amount", text: $amount)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                TextField("Min Out", text: $minOut)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                Button("Execute Route") {
                    let amountValue = Int(amount) ?? 1
                    let minOutValue = Int(minOut) ?? 1
                    Task {
                        await model.run(
                            module: "exchange",
                            action: "route_swap",
                            payload: [
                                "asset_in": assetIn,
                                "asset_out": assetOut,
                                "amount": amountValue,
                                "min_out": minOutValue,
                            ]
                        )
                    }
                }
                .buttonStyle(.borderedProminent)
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
                PreviewBanner(text: "Testnet Alpha. No accounts or live chat history.")
                RunInputsView(model: model)
                TextField("Channel", text: $channel)
                    .textFieldStyle(.roundedBorder)
                TextField("Message", text: $message)
                    .textFieldStyle(.roundedBorder)
                Button("Submit Event") {
                    Task {
                        await model.run(
                            module: "chat",
                            action: "message_event",
                            payload: ["channel": channel, "message": message]
                        )
                    }
                }
                .buttonStyle(.borderedProminent)
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
    @State private var quantity = "1"

    private let catalog: [String: (String, Int)] = [
        "sku-1": ("Signal Pack", 10),
        "sku-2": ("Orbit Node", 12),
        "sku-3": ("Trace Kit", 8),
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Alpha. Static catalog only.")
                RunInputsView(model: model)
                Picker("Item", selection: $sku) {
                    Text("Signal Pack").tag("sku-1")
                    Text("Orbit Node").tag("sku-2")
                    Text("Trace Kit").tag("sku-3")
                }
                .pickerStyle(.menu)
                TextField("Quantity", text: $quantity)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                Button("Create Order Intent") {
                    let qty = Int(quantity) ?? 1
                    let item = catalog[sku] ?? ("Signal Pack", 10)
                    Task {
                        await model.run(
                            module: "marketplace",
                            action: "order_intent",
                            payload: [
                                "sku": sku,
                                "title": item.0,
                                "price": item.1,
                                "qty": qty,
                            ]
                        )
                    }
                }
                .buttonStyle(.borderedProminent)
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
    @State private var mode = "pulse"
    @State private var step = "1"

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Alpha. Deterministic steps.")
                RunInputsView(model: model)
                Picker("Mode", selection: $mode) {
                    Text("Pulse").tag("pulse")
                    Text("Orbit").tag("orbit")
                    Text("Signal").tag("signal")
                }
                .pickerStyle(.segmented)
                TextField("Step", text: $step)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                Button("Execute Step") {
                    let stepValue = Int(step) ?? 0
                    Task {
                        await model.run(
                            module: "entertainment",
                            action: "state_step",
                            payload: ["mode": mode, "step": stepValue]
                        )
                    }
                }
                .buttonStyle(.borderedProminent)
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Entertainment")
            .background(SolsticePalette.background)
        }
    }
}

struct TrustView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Testnet Alpha. Evidence-first operations.")
                Text("Trust & Evidence")
                    .font(.title2)
                Text("No live mainnet data. Evidence is deterministic and replayable.")
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
