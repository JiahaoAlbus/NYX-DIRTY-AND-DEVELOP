import SwiftUI

struct ContentView: View {
    @StateObject private var settings = BackendSettings()
    
    var body: some View {
        AppShellView(settings: settings)
    }
}
