import Foundation

final class BackendSettings: ObservableObject {
    @Published var baseURL: String
    @Published var isDarkMode: Bool
    @Published var session: PortalSession?
    @Published var seed: String
    @Published var runIdBase: String

    private let sessionKey = "nyx_portal_session"
    private let seedKey = "nyx_seed"
    private let runIdKey = "nyx_run_id_base"

    init() {
        if let saved = UserDefaults.standard.string(forKey: "nyx_backend_url"), !saved.isEmpty {
            baseURL = saved
        } else {
            baseURL = GatewayClient.defaultBaseURLString()
        }
        isDarkMode = UserDefaults.standard.bool(forKey: "nyx_dark_mode") || (UserDefaults.standard.object(forKey: "nyx_dark_mode") == nil)
        seed = UserDefaults.standard.string(forKey: seedKey) ?? "123"
        runIdBase = UserDefaults.standard.string(forKey: runIdKey) ?? "ios-run-1"
        if let raw = UserDefaults.standard.string(forKey: sessionKey),
           let data = raw.data(using: .utf8) {
            session = try? JSONDecoder().decode(PortalSession.self, from: data)
        } else {
            session = nil
        }
    }

    func save() {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return
        }
        baseURL = trimmed
        UserDefaults.standard.set(trimmed, forKey: "nyx_backend_url")
        UserDefaults.standard.set(isDarkMode, forKey: "nyx_dark_mode")
        UserDefaults.standard.set(seed, forKey: seedKey)
        UserDefaults.standard.set(runIdBase, forKey: runIdKey)
    }

    func saveSession(_ next: PortalSession?) {
        session = next
        if let next = next, let data = try? JSONEncoder().encode(next) {
            UserDefaults.standard.set(String(data: data, encoding: .utf8), forKey: sessionKey)
        } else {
            UserDefaults.standard.removeObject(forKey: sessionKey)
        }
    }

    func logout() {
        saveSession(nil)
    }

    func resolvedURL() -> URL? {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        return URL(string: trimmed)
    }
}
