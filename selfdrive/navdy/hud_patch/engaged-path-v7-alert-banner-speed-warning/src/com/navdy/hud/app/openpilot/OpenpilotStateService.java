package com.navdy.hud.app.openpilot;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;

import com.navdy.hud.app.maps.widget.TrafficIncidentWidgetPresenter;

public final class OpenpilotStateService extends Service {
  private static final String TAG = "NavdyOpenpilotService";
  private static final int PORT = 8765;

  private static volatile boolean sStarted;

  @Override
  public int onStartCommand(Intent intent, int flags, int startId) {
    startServer(getApplicationContext());
    return START_STICKY;
  }

  @Override
  public IBinder onBind(Intent intent) {
    return null;
  }

  private static synchronized void startServer(Context context) {
    if (sStarted) {
      return;
    }
    sStarted = true;
    new Thread(new ServerRunnable(context), "NavdyOpenpilotSocket").start();
  }

  private static final class ServerRunnable implements Runnable {
    private final Context mContext;
    private final Handler mMainHandler;

    ServerRunnable(Context context) {
      mContext = context.getApplicationContext();
      mMainHandler = new Handler(Looper.getMainLooper());
    }

    @Override
    public void run() {
      while (true) {
        ServerSocket serverSocket = null;
        try {
          serverSocket = new ServerSocket(PORT, 1, InetAddress.getByName("127.0.0.1"));
          Log.i(TAG, "NavdyOpenpilotService listening port=" + PORT);
          while (true) {
            new Thread(new ClientRunnable(mContext, mMainHandler, serverSocket.accept()),
                "NavdyOpenpilotClient").start();
          }
        } catch (Throwable t) {
          Log.w(TAG, "socket server failed", t);
          sleepBeforeRestart();
        } finally {
          if (serverSocket != null) {
            try {
              serverSocket.close();
            } catch (Throwable ignored) {
            }
          }
        }
      }
    }

    private static void sleepBeforeRestart() {
      try {
        Thread.sleep(1000L);
      } catch (InterruptedException ignored) {
      }
    }
  }

  private static final class ClientRunnable implements Runnable {
    private final Context mContext;
    private final Handler mMainHandler;
    private final Socket mSocket;

    ClientRunnable(Context context, Handler mainHandler, Socket socket) {
      mContext = context;
      mMainHandler = mainHandler;
      mSocket = socket;
    }

    @Override
    public void run() {
      try {
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(mSocket.getInputStream(), "UTF-8"));
        BufferedWriter writer = new BufferedWriter(
            new OutputStreamWriter(mSocket.getOutputStream(), "UTF-8"));
        String line;
        while ((line = reader.readLine()) != null) {
          if (line.length() != 0) {
            dispatchPayload(line);
            writer.write("{\"cameraSpeedKph\":"
                + TrafficIncidentWidgetPresenter.getLastCameraSpeedLimit()
                + ",\"cameraSource\":\"trafficNotification\"}\n");
            writer.flush();
          }
        }
      } catch (Throwable t) {
        Log.w(TAG, "socket client failed", t);
      } finally {
        try {
          mSocket.close();
        } catch (Throwable ignored) {
        }
      }
    }

    private void dispatchPayload(final String payload) {
      mMainHandler.removeCallbacksAndMessages(mContext);
      mMainHandler.postAtTime(new Runnable() {
        @Override
        public void run() {
          OpenpilotStateReceiver.handleOpenpilotPayload(mContext, payload);
        }
      }, mContext, SystemClock.uptimeMillis());
    }
  }
}
