import AVFoundation

final class AudioService {
    static let shared = AudioService()
    private var player: AVAudioPlayer?

    func playForcedVoice(named key: String) {
        // Bundle resource e.g. voices/hi.wav — optional until assets synced
        guard let url = Bundle.main.url(forResource: key, withExtension: "wav", subdirectory: "voices")
                ?? Bundle.main.url(forResource: key, withExtension: "mp3") else { return }
        player = try? AVAudioPlayer(contentsOf: url)
        player?.play()
    }

    func stop() {
        player?.stop()
    }
}
