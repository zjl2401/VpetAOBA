import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject private var bridge: SharedBridge
    @State private var name = ""
    @State private var error = ""

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(red: 0.93, green: 0.95, blue: 0.90), Color(red: 0.82, green: 0.88, blue: 0.84)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 20) {
                Text("Vpet")
                    .font(.system(size: 42, weight: .bold, design: .rounded))
                    .foregroundStyle(Color(red: 0.18, green: 0.32, blue: 0.28))
                Text("认主后进入房间模式\n（iOS 无系统级悬浮窗）")
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.secondary)
                TextField("输入所属人昵称（最多16字）", text: $name)
                    .textFieldStyle(.roundedBorder)
                    .padding(.horizontal, 32)
                if !error.isEmpty {
                    Text(error).foregroundStyle(.red).font(.footnote)
                }
                Button("进入房间") {
                    let ok = bridge.setOwner(name)
                    if !ok { error = "请填写有效昵称" }
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(red: 0.22, green: 0.45, blue: 0.38))
            }
            .padding()
        }
    }
}
