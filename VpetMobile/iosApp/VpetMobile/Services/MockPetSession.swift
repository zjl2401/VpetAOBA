import Foundation

/// Pure-Swift stand-in for KMP `PetSession` so the iOS sources compile without the framework on Windows.
final class MockPetSession {
    private(set) var stamina: Int = 80
    private(set) var mood: Int = 80
    private(set) var mode: PetMode = .free

    private var owner: String = UserDefaults.standard.string(forKey: "mock_owner") ?? ""
    private var coinBalance: Int = UserDefaults.standard.object(forKey: "mock_coins") as? Int ?? 20
    private var foods: [String: Int] = [:]

    private let catalog: [(id: String, label: String, stamina: Int, mood: Int)] = [
        ("bread", "面包", 8, 3), ("apple", "苹果", 12, 6), ("cake", "蛋糕", 5, 14),
        ("fish", "烤鱼", 20, 4), ("onigiri", "饭团", 10, 5), ("candy", "糖果", 3, 12),
        ("tea", "热茶", 6, 8), ("meat", "烤肉", 18, 5), ("berry", "草莓", 8, 10),
        ("donut", "甜甜圈", 7, 11), ("milk", "牛奶", 9, 7), ("ramen", "拉面", 16, 8),
        ("sushi", "寿司", 14, 9), ("cookie", "曲奇", 4, 10), ("juice", "果汁", 7, 9),
        ("taco", "卷饼", 13, 6), ("icecream", "冰淇淋", 5, 13), ("corn", "玉米", 11, 4),
    ]

    init() {
        if let data = UserDefaults.standard.dictionary(forKey: "mock_foods") as? [String: Int] {
            foods = data
        } else {
            for item in catalog { foods[item.id] = 3 }
            persist()
        }
    }

    func ensureReady() { persist() }

    func hasOwner() -> Bool { !owner.isEmpty }
    func ownerName() -> String { owner }

    func setOwner(name: String) -> Bool {
        let trimmed = String(name.trimmingCharacters(in: .whitespacesAndNewlines).prefix(16))
        guard !trimmed.isEmpty, owner.isEmpty else { return false }
        owner = trimmed
        UserDefaults.standard.set(owner, forKey: "mock_owner")
        return true
    }

    func coins() -> Int { coinBalance }

    func grantCoins(_ n: Int) {
        coinBalance += max(0, n)
        persist()
    }

    func foodCounts() -> [(id: String, label: String, count: Int)] {
        catalog.map { ($0.id, $0.label, foods[$0.id] ?? 0) }
    }

    func feed(foodId: String) -> String {
        guard let item = catalog.first(where: { $0.id == foodId }) else { return "未知食物" }
        let c = foods[foodId] ?? 0
        guard c > 0 else { return "\(item.label) 数量不足" }
        foods[foodId] = c - 1
        stamina = min(100, stamina + item.stamina)
        mood = min(100, mood + item.mood)
        persist()
        return "喂了\(item.label) · 体力+\(item.stamina) 心情+\(item.mood)"
    }

    func setMode(_ m: PetMode) { mode = m }

    func launchGreeting() -> String? {
        guard hasOwner() else { return nil }
        if !UserDefaults.standard.bool(forKey: "mock_welcome_done") {
            UserDefaults.standard.set(true, forKey: "mock_welcome_done")
            return "\(owner)！从今天起就拜托你啦～"
        }
        return nil
    }

    func statusText() -> String {
        let label: String
        switch mode {
        case .free: label = "自由"
        case .follow: label = "跟随"
        case .stroll: label = "漫步"
        case .quiet: label = "睡眠"
        case .work: label = "工作"
        case .music: label = "音乐"
        case .none: label = "无"
        }
        return "体力 \(stamina) · 心情 \(mood) · 金币 \(coinBalance) · \(label)"
    }

    private func persist() {
        UserDefaults.standard.set(coinBalance, forKey: "mock_coins")
        UserDefaults.standard.set(foods, forKey: "mock_foods")
    }
}
