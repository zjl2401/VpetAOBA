import SwiftUI

@main
struct VpetMobileApp: App {
    @StateObject private var bridge = SharedBridge.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(bridge)
        }
    }
}
