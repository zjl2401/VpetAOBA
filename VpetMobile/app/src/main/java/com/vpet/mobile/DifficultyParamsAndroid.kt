package com.vpet.mobile

import android.content.Context

/** Android 桥：难度读 AppDataStore，逻辑在 shared [DifficultyParams]。 */
fun DifficultyParams.of(ctx: Context): DifficultyParams.Params =
    DifficultyParams.ofLabel(AppDataStore.difficulty(ctx))
