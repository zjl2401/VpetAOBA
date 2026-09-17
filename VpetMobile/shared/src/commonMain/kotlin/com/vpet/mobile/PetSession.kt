package com.vpet.mobile

enum class PetLocomotion { NONE, FREE, STROLL, FOLLOW, QUIET, WORK, MUSIC }

/**
 * iOS / 双端房间会话门面：认主、模式、喂食、面板数值。
 */
class PetSession {
    var stamina: Int = 80
        private set
    var mood: Int = 80
        private set
    var mode: PetLocomotion = PetLocomotion.FREE
        private set

    fun ensureReady() {
        SharedWalletStore.ensureFarmItems()
        SharedFoodInventoryStore.ensureSeeded()
        SharedWalletStore.tryDailyLoginCoin()
    }

    fun setOwner(name: String): Boolean = SharedPetProfileStore.setOwnerName(name)

    fun ownerName(): String = SharedPetProfileStore.ownerName()

    fun hasOwner(): Boolean = SharedPetProfileStore.hasOwner()

    fun coins(): Int = SharedWalletStore.coins()

    fun companionDays(): Int = SharedPetProfileStore.companionDays()

    fun foodCounts(): Map<String, Int> = SharedFoodInventoryStore.load().toMap()

    fun feed(foodId: String): String {
        val food = FoodCatalog.byId(foodId) ?: return "未知食物"
        if (!SharedFoodInventoryStore.consumeOne(foodId)) return "${food.label} 数量不足"
        stamina = (stamina + food.stamina).coerceIn(0, 100)
        mood = (mood + food.mood).coerceIn(0, 100)
        return "喂了${food.label} · 体力+${food.stamina} 心情+${food.mood}"
    }

    fun setMode(m: PetLocomotion) {
        mode = m
        val bucket = when (m) {
            PetLocomotion.FREE -> "free"
            PetLocomotion.FOLLOW -> "follow"
            PetLocomotion.STROLL -> "stroll"
            PetLocomotion.QUIET -> "quiet"
            PetLocomotion.WORK -> "work"
            PetLocomotion.MUSIC -> "music"
            PetLocomotion.NONE -> null
        }
        SharedModeTimeStore.setBucket(bucket)
    }

    fun launchGreeting(): String? = SharedPetProfileStore.consumeLaunchGreeting()

    fun statusText(): String =
        "体力 $stamina · 心情 $mood · 金币 ${coins()} · ${modeLabel()}"

    fun modeLabel(): String = when (mode) {
        PetLocomotion.FREE -> "自由"
        PetLocomotion.FOLLOW -> "跟随"
        PetLocomotion.STROLL -> "漫步"
        PetLocomotion.QUIET -> "睡眠"
        PetLocomotion.WORK -> "工作"
        PetLocomotion.MUSIC -> "音乐"
        PetLocomotion.NONE -> "无"
    }

    fun menuRoot(): List<DesktopMenuCatalog.Item> = DesktopMenuCatalog.root
}
