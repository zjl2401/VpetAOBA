import SwiftUI

struct HomeView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var bridge: SharedBridge
    @State private var outdoor = false
    @State private var toast = ""
    private let cols = 6
    private let rows = 5
    private let tools = ["锄地", "播种", "浇水", "收获", "砍树", "钓鱼", "采花"]

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                Picker("区域", selection: $outdoor) {
                    Text("室内").tag(false)
                    Text("户外").tag(true)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)

                let color = outdoor
                    ? Color(red: 0.55, green: 0.72, blue: 0.45)
                    : Color(red: 0.55, green: 0.58, blue: 0.65)

                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: cols), spacing: 4) {
                    ForEach(0..<(cols * rows), id: \.self) { i in
                        RoundedRectangle(cornerRadius: 4)
                            .fill(color.opacity(0.35 + Double((i + (outdoor ? 1 : 0)) % 3) * 0.15))
                            .aspectRatio(1, contentMode: .fit)
                            .overlay(
                                Text(outdoor ? "草" : "地")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            )
                    }
                }
                .padding(.horizontal)

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(tools, id: \.self) { t in
                            Button(t) {
                                toast = "\(t) · MVP（对等 Android 家园经营）"
                                if t == "收获" { bridge.grantCoins(2) }
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                    .padding(.horizontal)
                }

                if !toast.isEmpty {
                    Text(toast).font(.footnote).foregroundStyle(.secondary)
                }
                Spacer()
            }
            .padding(.top)
            .navigationTitle("家园")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") { dismiss() }
                }
            }
        }
    }
}
