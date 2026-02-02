import Foundation

final class BackendSettings: ObservableObject {
    @Published var baseURL: String
    @Published var isDarkMode: Bool

    init() {
        if let saved = UserDefaults.standard.string(forKey: "nyx_backend_url"), !saved.isEmpty {
            baseURL = saved
        } else {
            baseURL = GatewayClient.defaultBaseURLString()
        }
        isDarkMode = UserDefaults.standard.bool(forKey: "nyx_dark_mode") || (UserDefaults.standard.object(forKey: "nyx_dark_mode") == nil)
    }

    func save() {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return
        }
        baseURL = trimmed
        UserDefaults.standard.set(trimmed, forKey: "nyx_backend_url")
        UserDefaults.standard.set(isDarkMode, forKey: "nyx_dark_mode")
    }

    func resolvedURL() -> URL? {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        return URL(string: trimmed)
    }
}
