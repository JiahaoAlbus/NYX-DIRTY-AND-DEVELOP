import Foundation

final class BackendSettings: ObservableObject {
    @Published var baseURL: String

    init() {
        if let saved = UserDefaults.standard.string(forKey: "nyx_backend_url"), !saved.isEmpty {
            baseURL = saved
        } else {
            baseURL = GatewayClient.defaultBaseURLString()
        }
    }

    func save() {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return
        }
        baseURL = trimmed
        UserDefaults.standard.set(trimmed, forKey: "nyx_backend_url")
    }

    func resolvedURL() -> URL? {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        return URL(string: trimmed)
    }
}
