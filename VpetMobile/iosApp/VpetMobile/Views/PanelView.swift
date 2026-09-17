import SwiftUI

struct PanelView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var message = ""

    var body: some View {
        NavigationStack {
            List {
                Section("状态") {
                    Text("体力 \(bridge.stamina)")
                    Text("心情 \(bridge.mood)")
                    Text("金币 \(bridge.coins)")
                    Text("所属 \(bridge.ownerName)")
                }
                Section("喂食（18 种）") {
                    ForEach(bridge.foodCounts, id: \.id) { item in
                        Button {
                            message = bridge.feed(item.id)
                        } label: {
                            HStack {
                                Text(item.label)
                                Spacer()
                                Text("×\(item.count)").foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                if !message.isEmpty {
                    Section { Text(message).foregroundStyle(.secondary) }
                }
            }
            .navigationTitle("面板")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") { dismissHost() }
                }
            }
        }
    }

    @Environment(\.dismiss) private var dismiss
    private func dismissHost() { dismiss() }
}
