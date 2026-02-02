import SwiftUI

struct SettingsView: View {
    @ObservedObject var settings: BackendSettings
    @State private var status: String = ""
    private let client = GatewayClient()

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 12) {
                Text("Backend URL")
                    .font(.headline)
                TextField("http://127.0.0.1:8091", text: $settings.baseURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled(true)
                    .padding(8)
                    .background(RoundedRectangle(cornerRadius: 8).stroke(.secondary))
                
                Divider().padding(.vertical, 8)
                
                Toggle("Dark Mode", isOn: $settings.isDarkMode)
                    .font(.headline)
                    .onChange(of: settings.isDarkMode) { _ in
                        settings.save()
                    }
                
                Divider().padding(.vertical, 8)

                HStack {
                    Button("Save") {
                        settings.save()
                        status = "Saved"
                    }
                    .buttonStyle(.borderedProminent)
                    Button("Test Connection") {
                        Task {
                            await testConnection()
                        }
                    }
                    .buttonStyle(.bordered)
                }
                Text(status)
                    .font(.footnote)
                    .foregroundColor(.secondary)
                Spacer()
            }
            .padding()
            .navigationTitle("Settings")
        }
    }

    @MainActor
    private func testConnection() async {
        guard let url = settings.resolvedURL() else {
            status = "Invalid URL"
            return
        }
        client.setBaseURL(url)
        let ok = await client.checkBackendAvailability(timeoutSeconds: 3.0)
        status = ok ? "Backend available" : "Backend unavailable"
    }
}
