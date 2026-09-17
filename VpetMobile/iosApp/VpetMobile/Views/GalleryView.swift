import SwiftUI

struct GalleryView: View {
    var body: some View {
        Form {
            Section("画廊") {
                Text("最小导入：Mac 真机用 PhotosPicker / 文件导入；首版瘦包不同步 Android 全量 assets。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            Section("留声") {
                Text("用户音频导入占位；强制语音优先走 AudioService + shared PlatformAudio。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("画廊·留声")
    }
}
