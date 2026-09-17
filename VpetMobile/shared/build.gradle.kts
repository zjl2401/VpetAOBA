plugins {
    kotlin("multiplatform")
    id("com.android.library")
}

kotlin {
    androidTarget {
        compilations.all {
            kotlinOptions.jvmTarget = "17"
        }
    }

    val hostOs = System.getProperty("os.name").orEmpty()
    val enableIos = hostOs.contains("Mac", ignoreCase = true) ||
        (project.findProperty("vpet.enableIos") as String?) == "true"

    if (enableIos) {
        listOf(iosX64(), iosArm64(), iosSimulatorArm64()).forEach { target ->
            target.binaries.framework {
                baseName = "VpetShared"
                isStatic = true
            }
        }
    }

    sourceSets {
        commonMain.dependencies {}
        commonTest.dependencies {
            implementation(kotlin("test"))
        }
        androidMain.dependencies {}
    }
}

android {
    namespace = "com.vpet.shared"
    compileSdk = 34
    defaultConfig {
        minSdk = 26
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
