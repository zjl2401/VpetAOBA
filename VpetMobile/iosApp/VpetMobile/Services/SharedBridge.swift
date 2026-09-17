import Foundation
import Combine

enum PetMode: String {
    case free, follow, stroll, quiet, work, music, none
}

/// Bridges KMP `VpetShared` when embedded; otherwise uses [MockPetSession].
/// On Mac after embedding the framework, replace MockPetSession calls with:
/// `#if canImport(VpetShared)` → `PetSession()` from Kotlin/Native.
final class SharedBridge: ObservableObject {
    static let shared = SharedBridge()

    @Published private(set) var hasOwner: Bool = false
    @Published private(set) var ownerName: String = ""
    @Published private(set) var statusText: String = ""
    @Published private(set) var stamina: Int = 80
    @Published private(set) var mood: Int = 80
    @Published private(set) var coins: Int = 20
    @Published private(set) var mode: PetMode = .free
    @Published private(set) var foodCounts: [(id: String, label: String, count: Int)] = []

    private let session = MockPetSession()

    private init() {
        refresh()
    }

    func ensureReady() {
        session.ensureReady()
        refresh()
    }

    func setOwner(_ name: String) -> Bool {
        let ok = session.setOwner(name: name)
        refresh()
        return ok
    }

    func setMode(_ m: PetMode) {
        session.setMode(m)
        refresh()
    }

    func feed(_ foodId: String) -> String {
        let msg = session.feed(foodId: foodId)
        refresh()
        return msg
    }

    func launchGreeting() -> String? {
        session.launchGreeting()
    }

    func grantCoins(_ n: Int) {
        session.grantCoins(n)
        refresh()
    }

    private func refresh() {
        hasOwner = session.hasOwner()
        ownerName = session.ownerName()
        stamina = session.stamina
        mood = session.mood
        coins = session.coins()
        mode = session.mode
        statusText = session.statusText()
        foodCounts = session.foodCounts()
    }
}
