import SwiftUI

struct PreviewBanner: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.footnote)
            .padding(8)
            .frame(maxWidth: .infinity)
            .background(Color.yellow.opacity(0.2))
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
                PreviewBanner(text: "Preview only. No accounts. No live data.")
                Text("NYX Portal")
                    .font(.largeTitle)
                Text("Deterministic evidence flows only.")
                    .foregroundColor(.secondary)
                RunInputsView(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("World")
        }
    }
}

struct ExchangeView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var route = "basic"

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Preview only. No live market data.")
                RunInputsView(model: model)
                Picker("Route", selection: $route) {
                    Text("Basic").tag("basic")
                    Text("Split").tag("split")
                }
                .pickerStyle(.segmented)
                Button("Execute Route") {
                    Task {
                        await model.run(module: "exchange", action: "route_swap", payload: ["route": route])
                    }
                }
                .buttonStyle(.borderedProminent)
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Exchange")
        }
    }
}

struct ChatView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var message = "Hello"

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Preview only. No accounts or chat history.")
                RunInputsView(model: model)
                TextField("Message", text: $message)
                    .textFieldStyle(.roundedBorder)
                Button("Submit Event") {
                    Task {
                        await model.run(module: "chat", action: "message_event", payload: ["message": message])
                    }
                }
                .buttonStyle(.borderedProminent)
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Chat")
        }
    }
}

struct MarketplaceView: View {
    @ObservedObject var model: EvidenceViewModel
    @State private var itemId = "kit-01"
    @State private var quantity = "1"

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PreviewBanner(text: "Preview only. Static catalog.")
                RunInputsView(model: model)
                Picker("Item", selection: $itemId) {
                    Text("Solar Kit").tag("kit-01")
                    Text("Signal Pod").tag("pod-02")
                    Text("Trace Pack").tag("trace-03")
                }
                .pickerStyle(.menu)
                TextField("Quantity", text: $quantity)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                Button("Create Order Intent") {
                    let qty = Int(quantity) ?? 1
                    Task {
                        await model.run(
                            module: "marketplace",
                            action: "order_intent",
                            payload: ["item_id": itemId, "quantity": qty]
                        )
                    }
                }
                .buttonStyle(.borderedProminent)
                EvidenceSummary(model: model)
                Spacer()
            }
            .padding()
            .navigationTitle("Marketplace")
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
                PreviewBanner(text: "Preview only. Deterministic steps.")
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
        .background(Color.yellow.opacity(0.1))
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
        }
    }
}
