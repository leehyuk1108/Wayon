package com.example.carcontroller.wear

import android.util.Log
import com.example.carcontroller.BuildConfig
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import com.google.android.gms.wearable.WearableListenerService
import com.google.firebase.database.ktx.database
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import org.json.JSONObject

class WearCommandService : WearableListenerService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val database by lazy {
        if (BuildConfig.FIREBASE_CONFIGURED) {
            Firebase.database(BuildConfig.FIREBASE_DATABASE_URL).reference.child("car_status")
        } else {
            null
        }
    }

    override fun onMessageReceived(event: MessageEvent) {
        when (event.path) {
            WearPaths.COMMAND -> handleCommand(event)
            WearPaths.REFRESH -> handleRefresh(event)
            WearPaths.REQUEST_STATUS -> handleStatusRequest(event)
            WearPaths.REQUEST_CONFIG -> handleConfigRequest(event)
            else -> super.onMessageReceived(event)
        }
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private fun handleCommand(event: MessageEvent) {
        val command = event.data.toString(Charsets.UTF_8)
        if (command.isBlank()) {
            sendResult(event.sourceNodeId, "command", false, "empty command")
            return
        }

        scope.launch {
            val success = CarCommandClient.send(applicationContext, command)
            sendResult(event.sourceNodeId, command, success, if (success) "sent through phone" else "phone api key missing or command failed")
        }
    }

    private fun handleRefresh(event: MessageEvent) {
        val reference = database
        if (reference == null) {
            sendResult(event.sourceNodeId, "refresh", false, "firebase config missing")
            return
        }
        reference.child("cmd_refresh").setValue(System.currentTimeMillis())
            .addOnSuccessListener {
                sendResult(event.sourceNodeId, "refresh", true, "refresh requested through phone")
            }
            .addOnFailureListener {
                sendResult(event.sourceNodeId, "refresh", false, "refresh request failed")
            }
    }

    private fun handleStatusRequest(event: MessageEvent) {
        val reference = database
        if (reference == null) {
            sendResult(event.sourceNodeId, "status", false, "firebase config missing")
            return
        }
        reference.get()
            .addOnSuccessListener {
                WearSync.syncStatus(applicationContext, it)
                sendResult(event.sourceNodeId, "status", true, "status synced")
            }
            .addOnFailureListener {
                sendResult(event.sourceNodeId, "status", false, "status sync failed")
            }
    }

    private fun handleConfigRequest(event: MessageEvent) {
        val prefs = getSharedPreferences(com.example.carcontroller.MainActivity.PREFS_NAME, MODE_PRIVATE)
        WearSync.syncApiUrl(applicationContext, prefs.getString(com.example.carcontroller.MainActivity.PREF_KEY_API_URL, null))
        sendResult(event.sourceNodeId, "config", true, "config synced")
    }

    private fun sendResult(nodeId: String, action: String, success: Boolean, message: String) {
        val payload = JSONObject()
            .put("action", action)
            .put("success", success)
            .put("message", message)
            .put("time", System.currentTimeMillis())
            .toString()
            .toByteArray(Charsets.UTF_8)

        Wearable.getMessageClient(applicationContext)
            .sendMessage(nodeId, WearPaths.RESULT, payload)
            .addOnFailureListener { Log.w(TAG, "Failed to send wear result", it) }
    }

    private companion object {
        const val TAG = "WearCommandService"
    }
}
