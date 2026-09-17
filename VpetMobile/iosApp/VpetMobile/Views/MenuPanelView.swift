import SwiftUI

struct MenuPanelView: View {
    @Environment(\.dismiss) private var dismiss

    private let roots: [(String, [String])] = [
        ("模式", ["自由", "跟随", "漫步", "睡眠", "音乐", "工作", "游戏"]),
        ("面板", ["状态", "伴侣", "人格", "邀请(stub)"]),
        ("互动", ["动作", "表情", "对话", "工具"]),
        ("系统", ["我的", "设置", "社区", "重置", "退出"]),
    ]

    var body: some View {
        NavigationStack {
            List {
                ForEach(roots, id: \.0) { section in
                    Section(section.0) {
                        ForEach(section.1, id: \.self) { title in
                            Text(title)
                        }
                    }
                }
            }
            .navigationTitle("四大菜单")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") { dismiss() }
                }
            }
        }
    }
}
