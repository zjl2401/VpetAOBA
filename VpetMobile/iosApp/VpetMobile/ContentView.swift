import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var bridge: SharedBridge

    var body: some View {
        Group {
            if bridge.hasOwner {
                RoomView()
            } else {
                OnboardingView()
            }
        }
    }
}
