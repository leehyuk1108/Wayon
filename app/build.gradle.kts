import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

val localProperties = Properties().apply {
    val file = rootProject.file("local.properties")
    if (file.exists()) file.inputStream().use(::load)
}

fun String.asBuildConfigString(): String =
    "\"${replace("\\", "\\\\").replace("\"", "\\\"")}\""

fun configuredValue(propertyName: String, environmentName: String, defaultValue: String = ""): String =
    providers.gradleProperty(propertyName).orNull
        ?: localProperties.getProperty(propertyName)
        ?: System.getenv(environmentName)
        ?: defaultValue

val wayonCloudUrl = configuredValue(
    propertyName = "wayon.cloudUrl",
    environmentName = "WAYON_CLOUD_URL",
    defaultValue = "https://wayon-cloud.hyuklee.workers.dev",
).trimEnd('/')
android {
    namespace = "app.hylink.mobile"
    compileSdk {
        version = release(36)
    }

    defaultConfig {
        applicationId = "app.hylink.mobile"
        minSdk = 24
        targetSdk = 36
        versionCode = 2
        versionName = "1.1"

        buildConfigField(
            "String",
            "WAYON_CLOUD_URL",
            wayonCloudUrl.asBuildConfigString(),
        )
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        buildConfig = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    testImplementation(libs.junit)
    testImplementation("org.json:json:20240303")
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}
