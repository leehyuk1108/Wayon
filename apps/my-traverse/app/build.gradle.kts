import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

val localProperties = Properties().apply {
    val file = rootProject.file("local.properties")
    if (file.exists()) file.inputStream().use(::load)
}

if (file("google-services.json").isFile) {
    apply(plugin = "com.google.gms.google-services")
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
val wayonDeviceId = configuredValue("wayon.deviceId", "WAYON_DEVICE_ID")
val wayonPushRegistrationToken = configuredValue(
    "wayon.pushRegistrationToken",
    "WAYON_PUSH_REGISTRATION_TOKEN",
)
val wayonLiveToken = configuredValue("wayon.liveToken", "WAYON_LIVE_TOKEN")
val firebaseDatabaseUrl = configuredValue("firebase.databaseUrl", "FIREBASE_DATABASE_URL")
val firebaseConfigured = file("google-services.json").isFile && firebaseDatabaseUrl.isNotBlank()

android {
    namespace = "com.example.carcontroller"
    compileSdk {
        version = release(36)
    }

    defaultConfig {
        applicationId = "com.example.carcontroller"
        minSdk = 24
        targetSdk = 36
        versionCode = 7
        versionName = "1.21"

        buildConfigField(
            "String",
            "WAYON_CLOUD_URL",
            wayonCloudUrl.asBuildConfigString(),
        )
        buildConfigField("String", "WAYON_DEVICE_ID", wayonDeviceId.asBuildConfigString())
        buildConfigField(
            "String",
            "WAYON_PUSH_REGISTRATION_TOKEN",
            wayonPushRegistrationToken.asBuildConfigString(),
        )
        buildConfigField("String", "WAYON_LIVE_TOKEN", wayonLiveToken.asBuildConfigString())
        buildConfigField("String", "FIREBASE_DATABASE_URL", firebaseDatabaseUrl.asBuildConfigString())
        buildConfigField("boolean", "FIREBASE_CONFIGURED", firebaseConfigured.toString())

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".source"
            versionNameSuffix = "-source"
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
    implementation("com.google.android.gms:play-services-location:21.3.0")
    implementation("com.google.android.gms:play-services-wearable:18.2.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.8.1")
    testImplementation(libs.junit)
    testImplementation("org.json:json:20240303")
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
    implementation("com.google.firebase:firebase-database-ktx")
    implementation("com.google.firebase:firebase-messaging-ktx")

}
