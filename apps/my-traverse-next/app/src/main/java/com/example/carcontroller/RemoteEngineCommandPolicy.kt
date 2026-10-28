package com.example.carcontroller

import org.json.JSONObject

internal object RemoteEngineCommandPolicy {
    fun blockReason(command: String, details: JSONObject, driving: Boolean): String? {
        if (driving) return "주행 중에는 원격 시동을 제어할 수 없습니다."
        val raw = details.optJSONObject("rawStatus")
        val remote = details.optJSONObject("remoteStart")
        val remoteRunning = remote?.optBoolean("remainingTimeValid", false) == true
        if (command == "VEHICLE_STOP") {
            return if (remoteRunning) null else "원격 시동 상태가 아닙니다."
        }
        if (raw == null || raw.isNull("eng")) return "시동 상태를 확인하지 못했습니다."
        if (details.optJSONObject("vehicleState")?.optBoolean("engineRunning", false) == true) {
            return "이미 시동이 켜져 있습니다."
        }
        val hood = details.optJSONObject("closures")?.optJSONObject("hood")
        if (hood == null || hood.isNull("active")) return "후드 상태를 확인하지 못했습니다."
        if (hood.optBoolean("active")) return "후드가 열려 있습니다."
        if (remote == null || remote.isNull("remainingStarts")) return "원격 시동 가능 횟수를 확인하지 못했습니다."
        if (remote.optInt("remainingStarts", 0) <= 0) return "원격 시동 가능 횟수가 없습니다."
        return null
    }
}
