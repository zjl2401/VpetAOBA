import SwiftUI

struct RoomView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var toast = ""
    @State private var showPanel = false
    @State private var showMenu = false
    @State private var showHome = false
    @State private var showGames = false
    @State private var showTools = false

    private let modes: [(PetMode, String)] = [
        (.free, "自由"), (.follow, "跟随"), (.stroll, "漫步"),
        (.quiet, "睡眠"), (.work, "工作"), (.music, "音乐"),
    ]

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [Color(red: 0.90, green: 0.93, blue: 0.96), Color(red: 0.78, green: 0.86, blue: 0.82)],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()

                VStack(spacing: 16) {
                    Text(bridge.statusText)
                        .font(.subheadline.monospacedDigit())
                        .padding(.top, 8)

                    ZStack {
                        Circle()
                            .fill(Color(red: 0.55, green: 0.72, blue: 0.62))
                            .frame(width: 160, height: 160)
                            .shadow(radius: 8, y: 4)
                        Text("苍叶")
                            .font(.title2.bold())
                            .foregroundStyle(.white)
                    }
                    .padding(.vertical, 24)
                    .onTapGesture { showMenu = true }

                    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), spacing: 8) {
                        ForEach(modes, id: \.1) { item in
                            Button(item.1) {
                                bridge.setMode(item.0)
                                toast = "模式：\(item.1)"
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                    .padding(.horizontal)

                    HStack(spacing: 12) {
                        Button("面板") { showPanel = true }
                        Button("家园") { showHome = true }
                        Button("游戏") { showGames = true }
                        Button("工具") { showTools = true }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(Color(red: 0.25, green: 0.42, blue: 0.48))

                    if !toast.isEmpty {
                        Text(toast).font(.footnote).foregroundStyle(.secondary)
                    }
                    Spacer()
                }
            }
            .navigationTitle("房间 · \(bridge.ownerName)")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showPanel) { PanelView() }
            .sheet(isPresented: $showMenu) { MenuPanelView() }
            .sheet(isPresented: $showHome) { HomeView() }
            .sheet(isPresented: $showGames) { GamesHubView() }
            .sheet(isPresented: $showTools) { ToolsView() }
            .onAppear {
                bridge.ensureReady()
                if let g = bridge.launchGreeting() { toast = g }
            }
        }
    }
}
