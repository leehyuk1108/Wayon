package com.example.carcontroller.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorMatrix
import android.graphics.ColorMatrixColorFilter
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Rect
import android.graphics.RectF
import android.util.Log
import android.util.TypedValue
import android.view.View
import android.widget.RemoteViews
import com.example.carcontroller.MainActivity
import com.example.carcontroller.R
import com.example.carcontroller.WayonCloudFeed
import com.example.carcontroller.WayonCloudFeedParser
import com.example.carcontroller.WayonImpactStateStore
import com.example.carcontroller.VehicleRefreshScheduler
import java.io.File
import java.net.URL
import java.util.concurrent.Executors
import javax.net.ssl.HttpsURLConnection
import kotlin.math.PI
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan

class MiniHomeWidget4x2 : AppWidgetProvider() {
    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        MiniHomeWidgetStore.hydrateFromCachedFeed(context)
        MiniHomeWidgetUpdater.renderAll(context)
        MiniHomeWidgetUpdater.requestMapRefresh(context)
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == MiniHomeWidgetUpdater.ACTION_DATA_CHANGED ||
            intent.action == MiniHomeWidgetUpdater.ACTION_REFRESH_MAP
        ) {
            if (!MiniHomeWidgetUpdater.hasWidgets(context)) return
            val pending = goAsync()
            MiniHomeWidgetUpdater.renderAll(context)
            MiniHomeWidgetUpdater.execute {
                try {
                    MiniHomeMapRenderer.refreshIfNeeded(context, MiniHomeWidgetStore.read(context))
                    MiniHomeWidgetUpdater.renderAll(context)
                } finally {
                    pending.finish()
                }
            }
            return
        }
        super.onReceive(context, intent)
    }
}

class MiniHomeWidget2x2 : AppWidgetProvider() {
    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        MiniHomeWidgetStore.hydrateFromCachedFeed(context)
        MiniHomeWidgetUpdater.renderAll(context)
        MiniHomeWidgetUpdater.requestMapRefresh(context)
    }
}

internal object MiniHomeWidgetStore {
    private const val PREFS = "mini_home_widget"
    private const val KEY_STATUS_KICKER = "status_kicker"
    private const val KEY_STATUS_TITLE = "status_title"
    private const val KEY_STATUS_DETAIL = "status_detail"
    private const val KEY_STATUS_TONE = "status_tone"
    private const val KEY_RANGE_KM = "range_km"
    private const val KEY_FUEL_PERCENT = "fuel_percent"
    private const val KEY_LATITUDE = "latitude"
    private const val KEY_LONGITUDE = "longitude"
    private const val KEY_UPDATED_AT = "updated_at"
    private const val KEY_TRACKING = "tracking"
    private const val MISSING_INT = -1

    fun updateFromFeed(context: Context, feed: WayonCloudFeed) {
        val snapshot = MiniHomeWidgetPolicy.snapshot(feed).let {
            if (WayonImpactStateStore.currentJson(context) == null) it
            else it.copy(status = MiniHomeWidgetPolicy.status(feed, impactActive = true))
        }
        preferences(context).edit()
            .putString(KEY_STATUS_KICKER, snapshot.status.kicker)
            .putString(KEY_STATUS_TITLE, snapshot.status.title)
            .putString(KEY_STATUS_DETAIL, snapshot.status.detail)
            .putString(KEY_STATUS_TONE, snapshot.status.tone)
            .putInt(KEY_RANGE_KM, snapshot.rangeKm ?: MISSING_INT)
            .putInt(KEY_FUEL_PERCENT, snapshot.fuelPercent ?: MISSING_INT)
            .putString(KEY_LATITUDE, snapshot.latitude?.toString())
            .putString(KEY_LONGITUDE, snapshot.longitude?.toString())
            .putString(KEY_UPDATED_AT, snapshot.updatedAt)
            .putBoolean(KEY_TRACKING, snapshot.tracking)
            .apply()
        MiniHomeWidgetUpdater.notifyDataChanged(context)
    }

    fun hydrateFromCachedFeed(context: Context) {
        if (preferences(context).contains(KEY_STATUS_TITLE)) return
        val cached = VehicleRefreshScheduler.cachedPassiveFeed(context) ?: return
        runCatching { WayonCloudFeedParser.parse(cached) }
            .onSuccess { updateFromFeed(context, it) }
            .onFailure { Log.w("MiniHomeWidget", "Cached feed could not seed widget: ${it.message}") }
    }

    fun read(context: Context): MiniHomeSnapshot {
        val prefs = preferences(context)
        val legacy = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
        val legacyRange = legacy.getString("range", null)?.let(::firstInteger)
        val legacyFuel = legacy.getString("fuel", null)?.let(::firstInteger)?.coerceIn(0, 100)
        return MiniHomeSnapshot(
            status = MiniHomeStatus(
                kicker = prefs.getString(KEY_STATUS_KICKER, "CHECK STATUS") ?: "CHECK STATUS",
                title = prefs.getString(KEY_STATUS_TITLE, "CHECKING") ?: "CHECKING",
                detail = prefs.getString(KEY_STATUS_DETAIL, "Waiting for vehicle data")
                    ?: "Waiting for vehicle data",
                tone = prefs.getString(KEY_STATUS_TONE, "offline") ?: "offline",
            ),
            rangeKm = prefs.getInt(KEY_RANGE_KM, MISSING_INT).takeIf { it >= 0 } ?: legacyRange,
            fuelPercent = prefs.getInt(KEY_FUEL_PERCENT, MISSING_INT).takeIf { it >= 0 } ?: legacyFuel,
            latitude = prefs.getString(KEY_LATITUDE, null)?.toDoubleOrNull(),
            longitude = prefs.getString(KEY_LONGITUDE, null)?.toDoubleOrNull(),
            updatedAt = prefs.getString(KEY_UPDATED_AT, "--") ?: "--",
            tracking = prefs.getBoolean(KEY_TRACKING, false),
        )
    }

    private fun preferences(context: Context) =
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun firstInteger(value: String): Int? = Regex("\\d+(?:\\.\\d+)?")
        .find(value)
        ?.value
        ?.toDoubleOrNull()
        ?.toInt()
}

internal object MiniHomeWidgetUpdater {
    const val ACTION_DATA_CHANGED = "com.example.carcontroller.MINI_HOME_DATA_CHANGED"
    const val ACTION_REFRESH_MAP = "com.example.carcontroller.MINI_HOME_REFRESH_MAP"
    private val executor = Executors.newSingleThreadExecutor()

    fun execute(block: () -> Unit) = executor.execute(block)

    fun notifyDataChanged(context: Context) {
        context.sendBroadcast(
            Intent(context, MiniHomeWidget4x2::class.java).setAction(ACTION_DATA_CHANGED),
        )
    }

    fun requestMapRefresh(context: Context) {
        context.sendBroadcast(
            Intent(context, MiniHomeWidget4x2::class.java).setAction(ACTION_REFRESH_MAP),
        )
    }

    fun renderAll(context: Context) {
        val manager = AppWidgetManager.getInstance(context)
        renderProvider(context, manager, MiniHomeWidget4x2::class.java, R.layout.widget_mini_home_4x2, wide = true)
        renderProvider(context, manager, MiniHomeWidget2x2::class.java, R.layout.widget_mini_home_2x2, wide = false)
    }

    fun hasWidgets(context: Context): Boolean {
        val manager = AppWidgetManager.getInstance(context)
        return manager.getAppWidgetIds(ComponentName(context, MiniHomeWidget4x2::class.java)).isNotEmpty() ||
            manager.getAppWidgetIds(ComponentName(context, MiniHomeWidget2x2::class.java)).isNotEmpty()
    }

    private fun renderProvider(
        context: Context,
        manager: AppWidgetManager,
        provider: Class<*>,
        layout: Int,
        wide: Boolean,
    ) {
        val ids = manager.getAppWidgetIds(ComponentName(context, provider))
        if (ids.isEmpty()) return
        val snapshot = MiniHomeWidgetStore.read(context).let { stored ->
            if (WayonImpactStateStore.currentJson(context) == null) stored
            else stored.copy(
                status = MiniHomeStatus("ATTENTION", "IMPACT\nDETECTED", "Check 360 Live", "critical"),
            )
        }
        val map = MiniHomeMapRenderer.cachedBitmap(context, wide)
        ids.forEach { id ->
            val views = RemoteViews(context.packageName, layout)
            views.setTextViewText(R.id.mini_home_kicker, snapshot.status.kicker)
            views.setTextViewText(R.id.mini_home_status, snapshot.status.title)
            views.setTextViewTextSize(
                R.id.mini_home_status,
                TypedValue.COMPLEX_UNIT_SP,
                statusTextSize(snapshot.status.title, wide),
            )
            views.setTextViewText(R.id.mini_home_detail, snapshot.status.detail)
            views.setViewVisibility(
                R.id.mini_home_detail,
                if (!wide || snapshot.status.detail.isBlank()) View.GONE else View.VISIBLE,
            )
            views.setTextViewText(R.id.mini_home_range, snapshot.rangeKm?.toString() ?: "--")
            views.setTextViewText(R.id.mini_home_updated, snapshot.updatedAt)
            views.setTextViewText(R.id.mini_home_fuel, snapshot.fuelPercent?.let { "$it%" } ?: "--")
            views.setProgressBar(R.id.mini_home_fuel_bar, 100, snapshot.fuelPercent ?: 0, false)
            views.setInt(
                R.id.mini_home_kicker,
                "setBackgroundResource",
                toneBackground(snapshot.status.tone),
            )
            views.setTextColor(
                R.id.mini_home_kicker,
                if (snapshot.status.tone == "offline") Color.WHITE else Color.rgb(20, 21, 23),
            )
            if (map != null) views.setImageViewBitmap(R.id.mini_home_map, map)
            else views.setImageViewResource(R.id.mini_home_map, R.drawable.widget_mini_home_map_placeholder)

            val openApp = Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            }
            views.setOnClickPendingIntent(
                R.id.mini_home_root,
                PendingIntent.getActivity(
                    context,
                    id,
                    openApp,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
                ),
            )
            manager.updateAppWidget(id, views)
        }
    }

    private fun toneBackground(tone: String): Int = when (tone) {
        "critical" -> R.drawable.widget_status_critical
        "warning" -> R.drawable.widget_status_warning
        "driving" -> R.drawable.widget_status_driving
        "running" -> R.drawable.widget_status_running
        "active" -> R.drawable.widget_status_active
        "offline" -> R.drawable.widget_status_offline
        else -> R.drawable.widget_status_secure
    }

    private fun statusTextSize(title: String, wide: Boolean): Float {
        val longestLine = title.lineSequence().maxOfOrNull(String::length) ?: 0
        return if (wide) {
            when {
                longestLine >= 12 -> 38f
                longestLine >= 9 -> 43f
                else -> 48f
            }
        } else {
            when {
                longestLine >= 12 -> 28f
                longestLine >= 9 -> 31f
                else -> 34f
            }
        }
    }
}

internal object MiniHomeMapRenderer {
    private const val ZOOM = 16
    private const val TILE_SIZE = 256
    private const val WIDE_WIDTH = 720
    private const val WIDE_HEIGHT = 360
    private const val SQUARE_SIZE = 480
    private const val MAP_MAX_AGE_MS = 6L * 60L * 60L * 1000L
    private const val MAP_MOVE_THRESHOLD_METERS = 100.0
    private const val TILE_MAX_AGE_MS = 14L * 24L * 60L * 60L * 1000L
    private const val PREFS = "mini_home_widget_map"
    private const val KEY_LATITUDE = "rendered_latitude"
    private const val KEY_LONGITUDE = "rendered_longitude"
    private const val KEY_RENDERED_AT = "rendered_at"
    private const val KEY_RENDER_VERSION = "render_version"
    private const val RENDER_VERSION = 5
    private const val TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile"

    @Synchronized
    fun refreshIfNeeded(context: Context, snapshot: MiniHomeSnapshot) {
        val latitude = snapshot.latitude ?: return
        val longitude = snapshot.longitude ?: return
        if (latitude !in -85.0..85.0 || longitude !in -180.0..180.0) return
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val oldLatitude = prefs.getString(KEY_LATITUDE, null)?.toDoubleOrNull()
        val oldLongitude = prefs.getString(KEY_LONGITUDE, null)?.toDoubleOrNull()
        val ageMs = System.currentTimeMillis() - prefs.getLong(KEY_RENDERED_AT, 0L)
        val renderVersion = prefs.getInt(KEY_RENDER_VERSION, 0)
        val movedMeters = if (oldLatitude != null && oldLongitude != null) {
            distanceMeters(oldLatitude, oldLongitude, latitude, longitude)
        } else {
            Double.MAX_VALUE
        }
        val wideFile = mapFile(context, wide = true)
        val squareFile = mapFile(context, wide = false)
        if (renderVersion == RENDER_VERSION && wideFile.isFile && squareFile.isFile &&
            movedMeters < MAP_MOVE_THRESHOLD_METERS && ageMs < MAP_MAX_AGE_MS
        ) {
            return
        }

        try {
            render(context, latitude, longitude, WIDE_WIDTH, WIDE_HEIGHT, wideFile)
            render(context, latitude, longitude, SQUARE_SIZE, SQUARE_SIZE, squareFile)
            prefs.edit()
                .putString(KEY_LATITUDE, latitude.toString())
                .putString(KEY_LONGITUDE, longitude.toString())
                .putLong(KEY_RENDERED_AT, System.currentTimeMillis())
                .putInt(KEY_RENDER_VERSION, RENDER_VERSION)
                .apply()
        } catch (error: Exception) {
            Log.w("MiniHomeWidget", "Map refresh failed: ${error.message}")
        }
    }

    fun cachedBitmap(context: Context, wide: Boolean): Bitmap? =
        mapFile(context, wide).takeIf(File::isFile)?.let { BitmapFactory.decodeFile(it.absolutePath) }

    private fun render(context: Context, latitude: Double, longitude: Double, width: Int, height: Int, output: File) {
        val worldTiles = 1 shl ZOOM
        val centerX = (longitude + 180.0) / 360.0 * worldTiles * TILE_SIZE
        val latRad = Math.toRadians(latitude.coerceIn(-85.05112878, 85.05112878))
        val centerY = (1.0 - ln(tan(latRad) + 1.0 / cos(latRad)) / PI) / 2.0 * worldTiles * TILE_SIZE
        val left = centerX - width / 2.0
        val top = centerY - height * 0.58
        val firstTileX = floor(left / TILE_SIZE).toInt()
        val lastTileX = floor((left + width - 1) / TILE_SIZE).toInt()
        val firstTileY = floor(top / TILE_SIZE).toInt()
        val lastTileY = floor((top + height - 1) / TILE_SIZE).toInt()
        val raw = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(raw)
        canvas.drawColor(Color.rgb(14, 15, 17))
        val tilePaint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG).apply {
            colorFilter = ColorMatrixColorFilter(ColorMatrix(floatArrayOf(
                0.86f, 0f, 0f, 0f, -48f,
                0f, 0.88f, 0f, 0f, -48f,
                0f, 0f, 0.91f, 0f, -47f,
                0f, 0f, 0f, 1f, 0f,
            )))
        }
        for (tileY in firstTileY..lastTileY) {
            if (tileY !in 0 until worldTiles) continue
            for (tileX in firstTileX..lastTileX) {
                val wrappedX = ((tileX % worldTiles) + worldTiles) % worldTiles
                val tile = loadTile(context, wrappedX, tileY) ?: continue
                val destinationLeft = (tileX * TILE_SIZE - left).toInt()
                val destinationTop = (tileY * TILE_SIZE - top).toInt()
                canvas.drawBitmap(
                    tile,
                    null,
                    Rect(destinationLeft, destinationTop, destinationLeft + TILE_SIZE, destinationTop + TILE_SIZE),
                    tilePaint,
                )
            }
        }

        drawVehicleMarker(canvas, width / 2f, height * 0.58f, width >= WIDE_WIDTH)
        val attributionPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.argb(145, 255, 255, 255)
            textSize = if (width >= WIDE_WIDTH) 13f else 11f
        }
        val attribution = "Esri"
        canvas.drawText(attribution, width - attributionPaint.measureText(attribution) - 10f, height - 9f, attributionPaint)

        val rounded = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val roundedCanvas = Canvas(rounded)
        val maskPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
        val radius = if (width >= WIDE_WIDTH) 32f else 28f
        roundedCanvas.drawRoundRect(RectF(0f, 0f, width.toFloat(), height.toFloat()), radius, radius, maskPaint)
        maskPaint.xfermode = PorterDuffXfermode(PorterDuff.Mode.SRC_IN)
        roundedCanvas.drawBitmap(raw, 0f, 0f, maskPaint)
        maskPaint.xfermode = null
        output.parentFile?.mkdirs()
        output.outputStream().use { rounded.compress(Bitmap.CompressFormat.PNG, 92, it) }
        raw.recycle()
        rounded.recycle()
    }

    private fun drawVehicleMarker(canvas: Canvas, x: Float, y: Float, wide: Boolean) {
        val scale = if (wide) 1f else 1.05f
        val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        paint.setShadowLayer(9f * scale, 0f, 3f * scale, Color.argb(190, 0, 0, 0))
        paint.color = Color.argb(135, 255, 255, 255)
        canvas.drawCircle(x, y, 34f * scale, paint)
        paint.clearShadowLayer()
        paint.color = Color.rgb(250, 250, 250)
        canvas.drawCircle(x, y, 17f * scale, paint)
        paint.color = Color.rgb(7, 8, 10)
        canvas.drawCircle(x, y, 4.6f * scale, paint)
    }

    private fun loadTile(context: Context, x: Int, y: Int): Bitmap? {
        val file = File(context.cacheDir, "mini_home_tiles/$ZOOM/$x/$y.png")
        if (file.isFile && System.currentTimeMillis() - file.lastModified() < TILE_MAX_AGE_MS) {
            return BitmapFactory.decodeFile(file.absolutePath)
        }
        val connection = (URL("$TILE_URL/$ZOOM/$y/$x").openConnection() as HttpsURLConnection).apply {
            connectTimeout = 7_000
            readTimeout = 7_000
            useCaches = true
            setRequestProperty("User-Agent", "MyTraverseNext/Widget")
        }
        return try {
            if (connection.responseCode !in 200..299) return null
            val bytes = connection.inputStream.use { it.readBytes() }
            file.parentFile?.mkdirs()
            file.writeBytes(bytes)
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        } finally {
            connection.disconnect()
        }
    }

    private fun mapFile(context: Context, wide: Boolean) =
        File(context.filesDir, "mini_home_widget/${if (wide) "map_4x2.png" else "map_2x2.png"}")

    internal fun distanceMeters(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val earthRadius = 6_371_000.0
        val latitude1 = Math.toRadians(lat1)
        val latitude2 = Math.toRadians(lat2)
        val deltaLatitude = latitude2 - latitude1
        val deltaLongitude = Math.toRadians(lon2 - lon1)
        val a = (sin(deltaLatitude / 2) * sin(deltaLatitude / 2) +
            cos(latitude1) * cos(latitude2) * sin(deltaLongitude / 2) * sin(deltaLongitude / 2)
            ).coerceIn(0.0, 1.0)
        return 2 * earthRadius * atan2(sqrt(a), sqrt(max(1e-12, 1 - a)))
    }
}
