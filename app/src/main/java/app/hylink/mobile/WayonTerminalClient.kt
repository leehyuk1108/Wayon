package app.hylink.mobile

import android.content.Context
import com.jcraft.jsch.ChannelShell
import com.jcraft.jsch.JSch
import com.jcraft.jsch.JSchException
import com.jcraft.jsch.KeyPair
import com.jcraft.jsch.Session
import com.jcraft.jsch.SocketFactory
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.io.PipedInputStream
import java.io.PipedOutputStream
import java.net.InetAddress
import java.net.Socket
import java.net.SocketAddress
import java.util.Properties
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

internal class WayonTerminalClient(
    private val context: Context,
    private val onState: (String, String) -> Unit,
    private val onOutput: (ByteArray) -> Unit,
) {
    private val executor = Executors.newSingleThreadExecutor()
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(15, TimeUnit.SECONDS)
        .build()
    private val disconnectRequested = AtomicBoolean(false)
    private val identityFile = File(context.filesDir, "wayon_terminal_rsa")
    private val publicKeyFile = File(context.filesDir, "wayon_terminal_rsa.pub")

    @Volatile private var session: Session? = null
    @Volatile private var channel: ChannelShell? = null
    @Volatile private var terminalInput: OutputStream? = null
    @Volatile private var bridge: WebSocketByteSocket? = null

    fun connect(websocketUrl: String, protocol: String) {
        disconnect()
        disconnectRequested.set(false)
        executor.execute {
            var terminalState = "closed"
            try {
                ensureIdentity()
                onState("connecting", "SSH 핸드셰이크")
                val jsch = JSch().apply { addIdentity(identityFile.absolutePath) }
                val socketFactory = WayonSocketFactory(httpClient, websocketUrl, protocol) {
                    bridge = it
                }
                val nextSession = jsch.getSession(SSH_USER, SSH_HOST, SSH_PORT).apply {
                    setSocketFactory(socketFactory)
                    setConfig(Properties().apply {
                        put("StrictHostKeyChecking", "no")
                        put("PreferredAuthentications", "publickey")
                        put("server_host_key", "ssh-ed25519,rsa-sha2-512,rsa-sha2-256,ssh-rsa")
                        put("PubkeyAcceptedAlgorithms", "rsa-sha2-512,rsa-sha2-256,ssh-rsa")
                    })
                }
                session = nextSession
                nextSession.connect(CONNECT_TIMEOUT_MS)

                val nextChannel = nextSession.openChannel("shell") as ChannelShell
                nextChannel.setPty(true)
                nextChannel.setPtyType("xterm-256color", 120, 40, 0, 0)
                channel = nextChannel
                val output = nextChannel.outputStream
                val input = nextChannel.inputStream
                terminalInput = output
                nextChannel.connect(CHANNEL_TIMEOUT_MS)
                terminalState = "connected"
                onState("connected", "OFFROAD 연결됨")

                val buffer = ByteArray(16 * 1024)
                while (!disconnectRequested.get() && nextChannel.isConnected) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    if (count > 0) onOutput(buffer.copyOf(count))
                }
            } catch (error: Exception) {
                if (!disconnectRequested.get()) {
                    val message = error.message.orEmpty()
                    if (error is JSchException && message.contains("auth fail", ignoreCase = true)) {
                        terminalState = "auth_required"
                        onState("auth_required", "SSH 키 등록 필요")
                    } else {
                        terminalState = "error"
                        onState("error", userMessage(error))
                    }
                }
            } finally {
                closeTransport()
                if (!disconnectRequested.get() && terminalState == "connected") {
                    onState("closed", "원격 세션 종료")
                }
            }
        }
    }

    fun send(text: String) {
        if (text.isEmpty()) return
        executor.execute {
            try {
                terminalInput?.apply {
                    write(text.toByteArray(Charsets.UTF_8))
                    flush()
                }
            } catch (error: IOException) {
                if (!disconnectRequested.get()) onState("error", "터미널 입력 전송에 실패했습니다.")
            }
        }
    }

    fun publicKey(): String {
        ensureIdentity()
        return publicKeyFile.readText(Charsets.UTF_8).trim()
    }

    fun disconnect() {
        disconnectRequested.set(true)
        closeTransport()
    }

    fun shutdown() {
        disconnect()
        executor.shutdownNow()
        httpClient.dispatcher.executorService.shutdown()
        httpClient.connectionPool.evictAll()
    }

    @Synchronized
    private fun ensureIdentity() {
        if (identityFile.isFile && publicKeyFile.isFile) return
        identityFile.delete()
        publicKeyFile.delete()
        val keyPair = KeyPair.genKeyPair(JSch(), KeyPair.RSA, 3072)
        try {
            keyPair.writePrivateKey(identityFile.absolutePath)
            keyPair.writePublicKey(publicKeyFile.absolutePath, "hylink-android")
            identityFile.setReadable(false, false)
            identityFile.setReadable(true, true)
            identityFile.setWritable(false, false)
            identityFile.setWritable(true, true)
        } finally {
            keyPair.dispose()
        }
    }

    @Synchronized
    private fun closeTransport() {
        runCatching { terminalInput?.close() }
        terminalInput = null
        runCatching { channel?.disconnect() }
        channel = null
        runCatching { session?.disconnect() }
        session = null
        runCatching { bridge?.close() }
        bridge = null
    }

    private fun userMessage(error: Exception): String {
        val message = error.message.orEmpty()
        return when {
            message.contains("device offline", true) || message.contains("1013") ->
                "차량이 Offroad인지 확인해 주세요."
            message.contains("timeout", true) -> "Wayon 터미널 연결 시간이 초과됐습니다."
            message.contains("unauthorized", true) -> "Wayon Cloud 키를 확인해 주세요."
            else -> message.take(120).ifBlank { "Wayon 원격 터미널 연결에 실패했습니다." }
        }
    }

    companion object {
        private const val SSH_USER = "comma"
        private const val SSH_HOST = "wayon-device"
        private const val SSH_PORT = 22
        private const val CONNECT_TIMEOUT_MS = 30_000
        private const val CHANNEL_TIMEOUT_MS = 10_000
    }
}

private class WayonSocketFactory(
    private val client: OkHttpClient,
    private val websocketUrl: String,
    private val protocol: String,
    private val onSocketCreated: (WebSocketByteSocket) -> Unit,
) : SocketFactory {
    lateinit var socket: WebSocketByteSocket
        private set

    override fun createSocket(host: String?, port: Int): Socket {
        socket = WebSocketByteSocket(client, websocketUrl, protocol)
        onSocketCreated(socket)
        socket.connect(null, 20_000)
        return socket
    }

    override fun getInputStream(socket: Socket): InputStream = socket.getInputStream()
    override fun getOutputStream(socket: Socket): OutputStream = socket.getOutputStream()
}

private class WebSocketByteSocket(
    private val client: OkHttpClient,
    private val websocketUrl: String,
    private val protocol: String,
) : Socket() {
    private val incoming = PipedInputStream(512 * 1024)
    private val incomingWriter = PipedOutputStream(incoming)
    private val opened = CountDownLatch(1)
    private val closed = AtomicBoolean(false)
    private val connected = AtomicBoolean(false)
    @Volatile private var failure: Throwable? = null
    @Volatile private var websocket: WebSocket? = null

    private val outgoing = object : OutputStream() {
        override fun write(value: Int) = write(byteArrayOf(value.toByte()), 0, 1)

        override fun write(buffer: ByteArray, offset: Int, length: Int) {
            if (!connected.get() || closed.get()) throw IOException("Wayon WebSocket is closed")
            val bytes = ByteString.of(*buffer.copyOfRange(offset, offset + length))
            if (websocket?.send(bytes) != true) throw IOException("Wayon WebSocket send failed")
        }
    }

    override fun connect(endpoint: SocketAddress?, timeout: Int) {
        if (connected.get()) return
        val request = Request.Builder()
            .url(websocketUrl)
            .header("Sec-WebSocket-Protocol", protocol)
            .header("User-Agent", "HylinkAndroid/terminal")
            .build()
        websocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                connected.set(true)
                opened.countDown()
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                if (!closed.get()) runCatching {
                    incomingWriter.write(bytes.toByteArray())
                    incomingWriter.flush()
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(code, reason)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                failure = if (code == 1000) null else IOException("Wayon WebSocket closed ($code): $reason")
                closeStreams()
                opened.countDown()
            }

            override fun onFailure(webSocket: WebSocket, throwable: Throwable, response: Response?) {
                failure = throwable
                closeStreams()
                opened.countDown()
            }
        })
        if (!opened.await(timeout.toLong().coerceAtLeast(1), TimeUnit.MILLISECONDS)) {
            close()
            throw IOException("Wayon WebSocket timeout")
        }
        failure?.let { throw IOException(it.message ?: "Wayon WebSocket failed", it) }
        if (!connected.get()) throw IOException("Wayon WebSocket did not connect")
    }

    override fun getInputStream(): InputStream = incoming
    override fun getOutputStream(): OutputStream = outgoing
    override fun isConnected(): Boolean = connected.get() && !closed.get()
    override fun isClosed(): Boolean = closed.get()
    override fun getInetAddress(): InetAddress = InetAddress.getLoopbackAddress()
    override fun setSoTimeout(timeout: Int) = Unit
    override fun setTcpNoDelay(on: Boolean) = Unit

    override fun close() {
        if (!closed.compareAndSet(false, true)) return
        connected.set(false)
        websocket?.close(1000, "Hylink terminal closed")
        closeStreams()
    }

    private fun closeStreams() {
        if (closed.compareAndSet(false, true)) connected.set(false)
        runCatching { incomingWriter.close() }
        runCatching { incoming.close() }
    }
}
