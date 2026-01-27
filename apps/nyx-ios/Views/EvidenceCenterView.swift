import SwiftUI

@MainActor
final class EvidenceCenterModel: ObservableObject {
    @Published var runs: [EvidenceRunSummary] = []
    @Published var status: String = "Idle"
    @Published var evidenceText: String = ""
    @Published var exportURL: URL?

    private let client = GatewayClient()

    func setBaseURL(_ base: String) {
        if let url = URL(string: base) {
            client.setBaseURL(url)
        }
    }

    func refreshRuns() async {
        status = "Loading runs..."
        do {
            runs = try await client.listRuns()
            status = runs.isEmpty ? "No runs yet" : "Runs loaded"
        } catch {
            status = "Backend unavailable"
        }
    }

    func loadEvidence(runId: String) async {
        status = "Loading evidence..."
        do {
            let raw = try await client.fetchEvidenceRaw(runId: runId)
            evidenceText = raw
            status = "Evidence ready"
        } catch {
            status = "Evidence fetch failed"
        }
    }

    func downloadExport(runId: String) async {
        status = "Downloading export..."
        do {
            let data = try await client.fetchExportZip(runId: runId)
            let url = FileManager.default.temporaryDirectory.appendingPathComponent("nyx-\(runId).zip")
            try data.write(to: url, options: .atomic)
            exportURL = url
            status = "Export ready"
        } catch {
            status = "Export failed"
        }
    }
}

struct EvidenceCenterView: View {
    @ObservedObject var settings: BackendSettings
    @StateObject private var model = EvidenceCenterModel()
    @State private var showShare = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                HStack {
                    Text("Evidence Center")
                        .font(.headline)
                    Spacer()
                    Button("Refresh") {
                        Task { await model.refreshRuns() }
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.horizontal)

                Text(model.status)
                    .font(.footnote)
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                List(model.runs) { run in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(run.runId)
                            .font(.subheadline)
                        if let status = run.status {
                            Text(status)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        HStack {
                            Button("Evidence") {
                                Task { await model.loadEvidence(runId: run.runId) }
                            }
                            .buttonStyle(.bordered)
                            Button("Export") {
                                Task {
                                    await model.downloadExport(runId: run.runId)
                                    if model.exportURL != nil { showShare = true }
                                }
                            }
                            .buttonStyle(.borderedProminent)
                        }
                    }
                }
                .listStyle(.plain)

                ScrollView {
                    Text(model.evidenceText)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                }
            }
            .navigationTitle("Evidence")
        }
        .onAppear {
            model.setBaseURL(settings.baseURL)
            Task { await model.refreshRuns() }
        }
        .onChange(of: settings.baseURL) { newValue in
            model.setBaseURL(newValue)
        }
        .sheet(isPresented: $showShare) {
            if let url = model.exportURL {
                ShareSheet(items: [url])
            }
        }
    }
}
