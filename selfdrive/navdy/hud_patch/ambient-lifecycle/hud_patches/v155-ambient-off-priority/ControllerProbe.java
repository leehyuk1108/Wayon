import android.content.Context;
import android.content.ContextWrapper;
import android.content.ContentResolver;
import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;
import java.io.File;
import java.lang.reflect.*;
import java.util.*;

/** Standalone ART test, never loaded by the HUD. No Looper loop or live GATT. */
public class ControllerProbe {
  static Class<?> cls;
  static ContentResolver resolver;
  static int checks;
  static byte[] off = {46, (byte)141, 4, 0, 0, 0, 0, 110};
  static void check(boolean value, String label) {
    if (!value) throw new AssertionError(label);
    checks++;
    System.out.println("PASS " + label);
  }
  static Field field(String name) throws Exception {
    Field f = cls.getDeclaredField(name); f.setAccessible(true); return f;
  }
  static void set(Object object, String name, Object value) throws Exception { field(name).set(object, value); }
  static Object get(Object object, String name) throws Exception { return field(name).get(object); }
  static Object call(Object object, String name, Class<?>[] types, Object... values) throws Exception {
    Method m = cls.getDeclaredMethod(name, types); m.setAccessible(true);
    try { return m.invoke(object, values); }
    catch (InvocationTargetException e) { throw new RuntimeException(name, e.getCause()); }
  }
  static void simple(Object o, String name) throws Exception { call(o, name, new Class<?>[]{}); }
  static void gear(Object o, String value) throws Exception { call(o,"setGearText",new Class<?>[]{String.class},value); }
  static void vehicle(Object o, boolean onroad, boolean door) throws Exception {
    call(o,"setVehicleState",new Class<?>[]{boolean.class,boolean.class},onroad,door);
  }
  static void send(Object o, byte[] packet) throws Exception { call(o,"sendPacket",new Class<?>[]{byte[].class},(Object)packet); }
  @SuppressWarnings("unchecked") static ArrayDeque<byte[]> queue(Object o) throws Exception { return (ArrayDeque<byte[]>)get(o,"mQueue"); }
  static void onlyOff(Object o, String label) throws Exception {
    ArrayDeque<byte[]> q=queue(o);
    check(!q.isEmpty(),label+" queued");
    for(byte[] p:q)check(Arrays.equals(p,off),label+" no stale ON/color");
  }
  static Object fresh() throws Exception {
    Context context = new ContextWrapper(null) {
      public Context getApplicationContext(){return this;}
      public ContentResolver getContentResolver(){return resolver;}
      public File getFilesDir(){return new File("/data/local/tmp/ambient-probe");}
      public Object getSystemService(String name){return null;}
    };
    // Initialize test-owned state without the constructor's Settings provider read.
    Class<?> unsafe=Class.forName("sun.misc.Unsafe");
    Object allocator=null;
    for(Field f:unsafe.getDeclaredFields())if(f.getType()==unsafe){f.setAccessible(true);allocator=f.get(null);break;}
    Object o=unsafe.getMethod("allocateInstance",Class.class).invoke(allocator,cls);
    Handler handler=new Handler(Looper.getMainLooper());
    set(o,"mHandler",handler);set(o,"mQueue",new ArrayDeque<byte[]>());set(o,"mContext",context);
    set(o,"mLastGear","");set(o,"mManualOverrideId","");set(o,"mLastAmbientBrightness",-1);
    String[] callbacks={"mStopScanRunnable","mReconnectRunnable","mConnectTimeoutRunnable",
        "mOverspeedStateRunnable","mBlinkRunnable","mWarningStepStartRunnable",
        "mWriteTimeoutRunnable","mWritePaceRunnable","mFlushAfterAckRunnable",
        "mBrightnessSyncRunnable","mAmbientFadeRunnable","mOffroadDelayedOffRunnable",
        "mOffroadDoorMaxRunnable","mOffroadDoorCloseRunnable","mManualOverrideExpiryRunnable",
        "mVehicleDataWatchdogRunnable"};
    for(int i=0;i<callbacks.length;i++){
      Constructor<?> c=Class.forName(cls.getName()+"$"+(i+3)).getDeclaredConstructor(cls);c.setAccessible(true);
      set(o,callbacks[i],c.newInstance(o));
    }
    Constructor<?> cb=Class.forName(cls.getName()+"$1").getDeclaredConstructor(cls);cb.setAccessible(true);
    Class<?> session=Class.forName("com.navdy.hud.app.ambient.AmbientGattSession");
    set(o,"mGattCallback",session.getConstructor(android.bluetooth.BluetoothGattCallback.class,Handler.class,Context.class)
        .newInstance(cb.newInstance(o),handler,context));
    // connectIfNeeded returns before acquiring a Bluetooth adapter. Never pump
    // the main Looper, so production timer callbacks run only when invoked here.
    set(o,"mConnecting",true);
    check(get(o,"mGatt")==null && get(o,"mAdapter")==null,"isolated transport");
    JSONObject p=new JSONObject("{\"enabled\":true,\"driving\":{\"zone1\":{\"enabled\":true,\"automaticBrightness\":false,\"brightness\":6},\"zone2\":{\"enabled\":true,\"brightness\":80}},\"reverseOff\":{\"enabled\":true},\"timing\":{\"fadeMilliseconds\":1000,\"doorCloseDelaySeconds\":20,\"doorMaxOnMinutes\":20,\"transitionUpdatesPerSecond\":30}}");
    set(o,"mProfile",p);
    return o;
  }
  static void fade(Object o,int a,int b) throws Exception {
    call(o,"startAmbientFade",new Class<?>[]{int.class,int.class,long.class},a,b,1000L);
  }
  public static void main(String[] args) throws Exception {
    try { run(); } catch(Throwable e){e.printStackTrace(System.out);System.exit(1);}
  }
  static void run() throws Exception {
    Looper.prepareMainLooper();
    Class<?> mock=Class.forName("android.test.mock.MockContentResolver");
    Context resolverContext=new ContextWrapper(null){
      public String getPackageName(){return "ambient.probe";}
      public String getOpPackageName(){return getPackageName();}
    };
    resolver=(ContentResolver)mock.getConstructor(Context.class).newInstance(resolverContext);
    mock.getMethod("addProvider",String.class,ContentProvider.class).invoke(resolver,"settings",new FakeSettings());
    cls=Class.forName("com.navdy.hud.app.ambient.AmbientLightController");
    Object o=fresh();
    byte[] on={46,(byte)141,4,0,72,50,80,(byte)164};
    byte[] color={46,(byte)141,8,1,8,1,2,3,4,5,6,7};
    vehicle(o,true,false);gear(o,"d");send(o,color);send(o,on);
    gear(o,"R");
    check((Boolean)get(o,"mReverseActive"),"R latch");onlyOff(o,"R preempts queued fade");
    vehicle(o,true,true);fade(o,20,100);send(o,color);send(o,on);
    onlyOff(o,"R blocks door/manual producer");
    call(o,"setOverspeed",new Class<?>[]{boolean.class},true);
    ((Runnable)get(o,"mBlinkRunnable")).run();
    ((Runnable)get(o,"mWarningStepStartRunnable")).run();
    onlyOff(o,"R blocks overspeed callbacks");
    simple(o,"restoreActiveStateAfterConnect");onlyOff(o,"reconnect in R restores OFF");
    gear(o,"unknown");check((Boolean)get(o,"mReverseActive"),"unknown gear cannot release R");
    gear(o,"d");check(!(Boolean)get(o,"mReverseActive"),"D releases R");
    check((Integer)get(o,"mAmbientTargetZone2")==100,"D while door open restores door brightness");
    vehicle(o,true,false);check((Integer)get(o,"mAmbientTargetZone2")==80,"closed onroad restores driving brightness");
    set(o,"mVehicleDataTimedOut",true);fade(o,100,100);send(o,on);
    simple(o,"restoreActiveStateAfterConnect");onlyOff(o,"data loss and reconnect stay OFF");
    vehicle(o,true,false);check(!(Boolean)get(o,"mVehicleDataTimedOut"),"fresh vehicle state recovers watchdog");
    check((Integer)get(o,"mAmbientTargetZone2")==80,"fresh data restores driving target");
    JSONObject profile=(JSONObject)get(o,"mProfile");
    JSONObject disabled=new JSONObject(profile.toString());disabled.put("enabled",false);
    call(o,"setAmbientProfile",new Class<?>[]{JSONObject.class},disabled);
    check(!(Boolean)get(o,"mAmbientActive"),"master OFF is inactive");
    check((Integer)get(o,"mLastAmbientBrightness")==-1,"master OFF stops brightness polling");
    call(o,"setAmbientProfile",new Class<?>[]{JSONObject.class},profile);
    check((Integer)get(o,"mLastAmbientBrightness")==6,"master ON restarts brightness polling");
    check((Integer)get(o,"mAmbientTargetZone2")==80,"master ON restores driving target");
    ((Handler)get(o,"mHandler")).removeCallbacksAndMessages(null);

    o=fresh();vehicle(o,true,false);gear(o,"d");
    set(o,"mCurrentZone1",6);set(o,"mCurrentZone2",80);
    vehicle(o,false,false);
    check((Integer)get(o,"mAmbientTargetZone1")==6&&(Integer)get(o,"mAmbientTargetZone2")==100,"offroad exit courtesy targets");
    vehicle(o,false,true);
    check((Integer)get(o,"mAmbientTargetZone1")==20&&(Integer)get(o,"mAmbientTargetZone2")==100,"offroad door targets");
    vehicle(o,false,false);
    check((Integer)get(o,"mAmbientTargetZone2")==100,"door close holds before timer");
    ((Runnable)get(o,"mOffroadDoorCloseRunnable")).run();
    check((Integer)get(o,"mAmbientTargetZone1")==0&&(Integer)get(o,"mAmbientTargetZone2")==0,"door close timer targets OFF");
    vehicle(o,false,true);((Runnable)get(o,"mOffroadDoorMaxRunnable")).run();
    check((Integer)get(o,"mAmbientTargetZone1")==0&&(Integer)get(o,"mAmbientTargetZone2")==0,"door maximum timer targets OFF");
    check(get(o,"mGatt")==null&&get(o,"mAdapter")==null,"no Bluetooth acquired throughout test");
    ((Handler)get(o,"mHandler")).removeCallbacksAndMessages(null);
    System.out.println("PASS actual APK controller checks="+checks+"; NO BLE transmissions; timer callbacks invoked, not elapsed-time proof");
    System.exit(0);
  }

  public static class FakeSettings extends ContentProvider {
    public boolean onCreate(){return true;}
    public Bundle call(String method,String arg,Bundle extras){
      if(method.startsWith("PUT_")){Bundle result=new Bundle();result.putBoolean("result",true);return result;}
      if(!method.startsWith("GET_"))throw new AssertionError("unexpected settings method");
      Bundle b=new Bundle();b.putString("value","100");return b;
    }
    public Cursor query(Uri u,String[] columns,String selection,String[] args,String sort){
      MatrixCursor c=new MatrixCursor(new String[]{"name","value"});c.addRow(new Object[]{"screen_brightness","100"});return c;
    }
    public String getType(Uri u){return null;}
    public Uri insert(Uri u,ContentValues v){throw new AssertionError("settings write");}
    public int delete(Uri u,String w,String[] a){throw new AssertionError("settings write");}
    public int update(Uri u,ContentValues v,String w,String[] a){throw new AssertionError("settings write");}
  }
}
