import SwiftUI
import WebKit

@MainActor
final class BackendHealthModel: ObservableObject {
    @Published var available: Bool = false
    @Published var statusText: String = "Backend: unknown"

    func check(baseURL: String) async {
        guard let url = URL(string: baseURL)?.appendingPathComponent("healthz") else {
            available = false
            statusText = "Backend: invalid URL"
            return
        }
        var request = URLRequest(url: url)
        request.timeoutInterval = 3
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let payload = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            let ok = payload?["ok"] as? Bool ?? false
            available = ok
            statusText = ok ? "Backend: available" : "Backend: unavailable"
        } catch {
            available = false
            statusText = "Backend: unavailable"
        }
    }
}

struct WebPortalView: View {
    @ObservedObject var settings: BackendSettings
    var initialScreen: String? = nil
    @StateObject private var health = BackendHealthModel()

    var body: some View {
        VStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 6) {
                Text("NYX Portal (Testnet)")
                    .font(.headline)
                Text(health.statusText)
                    .font(.footnote)
                    .foregroundColor(.secondary)
                if !health.available {
                    HStack {
                        Text("Backend Offline")
                            .font(.footnote)
                        Spacer()
                        Button("Retry") {
                            Task { await health.check(baseURL: settings.baseURL) }
                        }
                        .buttonStyle(.bordered)
                    }
                    .padding(8)
                    .background(Color.orange.opacity(0.2))
                    .cornerRadius(8)
                }
            }
            .padding()

            WebContainerView(backendURL: settings.baseURL, sessionToken: settings.session?.access_token, initialScreen: initialScreen)
                .id("\(settings.baseURL)-\(initialScreen ?? "default")")
                .edgesIgnoringSafeArea(.bottom)
        }
        .task {
            await health.check(baseURL: settings.baseURL)
        }
        .onChange(of: settings.baseURL) { newValue in
            Task { await health.check(baseURL: newValue) }
        }
    }
}

struct WebContainerView: UIViewRepresentable {
    let backendURL: String
    let sessionToken: String?
    let initialScreen: String?

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        
        let escapedURL = backendURL
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "'", with: "\\'")
        
        var scriptSource = "window.__NYX_BACKEND_URL__ = '\(escapedURL)';"
        
        if let token = sessionToken {
            let escapedToken = token.replacingOccurrences(of: "'", with: "\\'")
            scriptSource += "window.__NYX_SESSION_TOKEN__ = '\(escapedToken)';"
        }
        
        if let screen = initialScreen {
            let escapedScreen = screen.replacingOccurrences(of: "'", with: "\\'")
            scriptSource += "window.__NYX_INITIAL_SCREEN__ = '\(escapedScreen)';"
        }

        let userScript = WKUserScript(source: scriptSource, injectionTime: .atDocumentStart, forMainFrameOnly: true)
        config.userContentController.addUserScript(userScript)

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = .clear
        if let url = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "WebBundle") {
            webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        } else {
            let html = "<html><body><p>Web bundle missing.</p></body></html>"
            webView.loadHTMLString(html, baseURL: nil)
        }
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}
}
