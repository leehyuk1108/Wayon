package com.example.carcontroller.wear

import android.content.Context
import com.google.android.gms.wearable.PutDataMapRequest
import com.google.android.gms.wearable.Wearable
import com.google.firebase.database.DataSnapshot

object WearSync {
    fun syncApiUrl(context: Context, apiUrl: String?) {
        val request = PutDataMapRequest.create(WearPaths.API_CONFIG).apply {
            dataMap.putBoolean("hasApiUrl", !apiUrl.isNullOrBlank())
            dataMap.putString("apiUrl", apiUrl.orEmpty())
            dataMap.putLong("updatedAt", System.currentTimeMillis())
        }.asPutDataRequest().setUrgent()

        Wearable.getDataClient(context.applicationContext).putDataItem(request)
    }

    fun syncStatus(
        context: Context,
        range: String,
        battery: String,
        batteryLevel: String,
        mileage: String,
        fuel: String,
        lastUpdate: String,
        oil: String,
        tirePressure: String,
        tirePressureAll: String,
    ) {
        val request = PutDataMapRequest.create(WearPaths.STATUS).apply {
            dataMap.putString("range", range)
            dataMap.putString("battery", battery)
            dataMap.putString("batteryLevel", batteryLevel)
            dataMap.putString("mileage", mileage)
            dataMap.putString("fuel", fuel)
            dataMap.putString("lastUpdate", lastUpdate)
            dataMap.putString("oil", oil)
            dataMap.putString("tirePressure", tirePressure)
            dataMap.putString("tirePressureAll", tirePressureAll)
            dataMap.putLong("updatedAt", System.currentTimeMillis())
            dataMap.putString("source", "phone")
        }.asPutDataRequest().setUrgent()

        Wearable.getDataClient(context.applicationContext).putDataItem(request)
    }

    fun syncStatus(context: Context, snapshot: DataSnapshot) {
        val tirePressure = snapshot.child("tire_pressure").getValue(String::class.java) ?: "--"
        val rawTirePressureAll = snapshot.child("tire_pressure_all").getValue(String::class.java) ?: "--"
        val tirePressureAll = rawTirePressureAll.takeUnless { it.isBlank() || it == "--" } ?: tirePressure

        syncStatus(
            context = context,
            range = snapshot.child("range").getValue(String::class.java) ?: "--",
            battery = snapshot.child("battery").getValue(String::class.java) ?: "--",
            batteryLevel = snapshot.child("battery_level").getValue(String::class.java) ?: "--",
            mileage = snapshot.child("mileage").getValue(String::class.java) ?: "--",
            fuel = snapshot.child("fuel").getValue(String::class.java) ?: "--",
            lastUpdate = snapshot.child("last_update").getValue(String::class.java) ?: "",
            oil = snapshot.child("oil").getValue(String::class.java) ?: "--",
            tirePressure = tirePressure,
            tirePressureAll = tirePressureAll,
        )
    }
}
