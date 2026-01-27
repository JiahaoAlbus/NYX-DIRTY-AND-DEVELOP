import SwiftUI

struct AppShellView: View {
    @StateObject private var settings = BackendSettings()

    var body: some View {
        TabView {
            WebPortalView(settings: settings)
                .tabItem {
                    Label("World", systemImage: "globe")
                }
            EvidenceCenterView(settings: settings)
                .tabItem {
                    Label("Evidence", systemImage: "doc.plaintext")
                }
            SettingsView(settings: settings)
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
    }
}
