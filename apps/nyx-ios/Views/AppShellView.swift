import SwiftUI

struct AppShellView: View {
    @ObservedObject var settings: BackendSettings
    @State private var selectedTab = 0
    
    var body: some View {
        Group {
            if settings.session == nil {
                PortalAuthView(settings: settings)
            } else {
                ZStack(alignment: .bottom) {
                    TabView(selection: $selectedTab) {
                        NYXHomeView(settings: settings, selectedTab: $selectedTab)
                            .tag(0)

                        NYXWalletView(settings: settings)
                            .tag(1)

                        WebPortalView(settings: settings, initialScreen: "exchange")
                            .tag(2)

                        WebPortalView(settings: settings, initialScreen: "chat")
                            .tag(3)

                        WebPortalView(settings: settings, initialScreen: "store")
                            .tag(4)

                        WebPortalView(settings: settings, initialScreen: "activity")
                            .tag(5)

                        SettingsView(settings: settings)
                            .tag(6)
                    }

                    // Custom Glassmorphic Tab Bar
                    HStack {
                        TabItem(icon: "house.fill", label: "Home", isSelected: selectedTab == 0) { selectedTab = 0 }
                        TabItem(icon: "wallet.pass.fill", label: "Wallet", isSelected: selectedTab == 1) { selectedTab = 1 }
                        TabItem(icon: "arrow.left.arrow.right.circle.fill", label: "Trade", isSelected: selectedTab == 2) { selectedTab = 2 }
                        TabItem(icon: "bubble.left.and.bubble.right.fill", label: "Chat", isSelected: selectedTab == 3) { selectedTab = 3 }
                        TabItem(icon: "bag.fill", label: "Store", isSelected: selectedTab == 4) { selectedTab = 4 }
                        TabItem(icon: "checkmark.seal.fill", label: "Proof", isSelected: selectedTab == 5) { selectedTab = 5 }
                        TabItem(icon: "gearshape.fill", label: "Settings", isSelected: selectedTab == 6) { selectedTab = 6 }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 12)
                    .background(.ultraThinMaterial)
                    .cornerRadius(25)
                    .padding(.horizontal)
                    .padding(.bottom, 10)
                }
                .edgesIgnoringSafeArea(.bottom)
            }
        }
        .preferredColorScheme(settings.isDarkMode ? .dark : .light)
    }
}

struct TabItem: View {
    let icon: String
    let label: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 20, weight: isSelected ? .bold : .medium))
                Text(label)
                    .font(.system(size: 10, weight: .bold))
            }
            .foregroundColor(isSelected ? .yellow : .secondary)
            .frame(maxWidth: .infinity)
        }
    }
}
