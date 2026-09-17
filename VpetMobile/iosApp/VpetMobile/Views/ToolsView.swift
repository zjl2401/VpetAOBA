import SwiftUI

struct ToolsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var swRunning = false
    @State private var swElapsed: TimeInterval = 0
    @State private var swTimer: Timer?
    @State private var pomoLeft = 25 * 60
    @State private var pomoTimer: Timer?
    @State private var bMonth = 1
    @State private var bDay = 1
    @State private var scheduleText = ""
    @State private var schedules: [String] = []

    var body: some View {
        NavigationStack {
            Form {
                Section("秒表") {
                    Text(format(swElapsed)).font(.title.monospacedDigit())
                    HStack {
                        Button(swRunning ? "暂停" : "开始") { toggleStopwatch() }
                        Button("复位") {
                            swTimer?.invalidate()
                            swRunning = false
                            swElapsed = 0
                        }
                    }
                }
                Section("番茄 25/5") {
                    Text(format(TimeInterval(pomoLeft))).font(.title.monospacedDigit())
                    HStack {
                        Button("开始番茄") { startPomo() }
                        Button("结束") {
                            pomoTimer?.invalidate()
                            pomoLeft = 25 * 60
                        }
                    }
                }
                Section("生日") {
                    Stepper("月 \(bMonth)", value: $bMonth, in: 1...12)
                    Stepper("日 \(bDay)", value: $bDay, in: 1...31)
                    Text("已设 \(bMonth)/\(bDay)（本地）")
                }
                Section("日程") {
                    TextField("事项", text: $scheduleText)
                    Button("添加") {
                        let t = scheduleText.trimmingCharacters(in: .whitespaces)
                        guard !t.isEmpty else { return }
                        schedules.append(t)
                        scheduleText = ""
                    }
                    ForEach(schedules, id: \.self) { Text($0) }
                }
                Section("画廊 / 留声") {
                    NavigationLink("打开") { GalleryView() }
                }
            }
            .navigationTitle("工具")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") { dismiss() }
                }
            }
            .onDisappear {
                swTimer?.invalidate()
                pomoTimer?.invalidate()
            }
        }
    }

    private func format(_ t: TimeInterval) -> String {
        let s = Int(t)
        return String(format: "%02d:%02d", s / 60, s % 60)
    }

    private func toggleStopwatch() {
        if swRunning {
            swTimer?.invalidate()
            swRunning = false
        } else {
            swRunning = true
            swTimer = Timer.scheduledTimer(withTimeInterval: 0.2, repeats: true) { _ in
                swElapsed += 0.2
            }
        }
    }

    private func startPomo() {
        pomoTimer?.invalidate()
        pomoLeft = 25 * 60
        pomoTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { timer in
            if pomoLeft <= 0 {
                timer.invalidate()
            } else {
                pomoLeft -= 1
            }
        }
    }
}
