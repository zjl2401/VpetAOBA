import SwiftUI

struct GamesHubView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                NavigationLink("采集") { CollectMiniView() }
                NavigationLink("暴露") { ExposeMiniView() }
                NavigationLink("音游") { RhythmMiniView() }
                NavigationLink("莱姆") { RhymeMiniView() }
                NavigationLink("RPG 简战") { RpgMiniView() }
            }
            .navigationTitle("游戏")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") { dismiss() }
                }
            }
        }
    }
}

struct CollectMiniView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var score = 0
    var body: some View {
        VStack(spacing: 16) {
            Text("点苹果采集 · 得分 \(score)")
            Button("🍎") {
                score += 1
                if score % 5 == 0 { bridge.grantCoins(1) }
            }
            .font(.system(size: 64))
        }
        .navigationTitle("采集")
    }
}

struct ExposeMiniView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var hits = 0
    @State private var msg = "在绿区内连点 5 次"
    var body: some View {
        VStack(spacing: 20) {
            Text(msg)
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.green.opacity(0.35))
                .frame(height: 120)
                .overlay(Text("暴露区").bold())
                .onTapGesture {
                    hits += 1
                    if hits >= 5 {
                        msg = "清除！心情+5"
                        bridge.grantCoins(2)
                        hits = 0
                    } else {
                        msg = "命中 \(hits)/5"
                    }
                }
        }
        .padding()
        .navigationTitle("暴露")
    }
}

struct RhythmMiniView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var last = "点按判定"
    var body: some View {
        VStack(spacing: 16) {
            Text(last).font(.title2)
            Button("打击") {
                let grades = ["S", "A", "B", "C", "D"]
                let g = grades.randomElement()!
                last = "评级 \(g)"
                let coins = ["S": 12, "A": 8, "B": 5, "C": 3, "D": 1][g] ?? 1
                bridge.grantCoins(coins)
            }
            .buttonStyle(.borderedProminent)
        }
        .navigationTitle("音游")
    }
}

struct RhymeMiniView: View {
    @EnvironmentObject private var bridge: SharedBridge
    var body: some View {
        VStack(spacing: 16) {
            Text("莱姆对决（简版）")
            Button("胜利 clear") {
                bridge.grantCoins(5)
            }
            .buttonStyle(.borderedProminent)
            Button("失败 hold") {}
                .buttonStyle(.bordered)
        }
        .navigationTitle("莱姆")
    }
}

struct RpgMiniView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var log = "遭遇史莱姆！"
    var body: some View {
        VStack(spacing: 12) {
            Text(log)
            Button("攻击") {
                log = "胜利！金币+3"
                bridge.grantCoins(3)
            }
            .buttonStyle(.borderedProminent)
            Button("逃跑") { log = "逃走了…" }
        }
        .navigationTitle("RPG")
    }
}
