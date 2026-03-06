package com.system.update.core;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

public class HeartbeatWorker extends Worker {

    public HeartbeatWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull
    @Override
    public Result doWork() {
        NetworkClient.sendHeartbeat(getApplicationContext());
        return Result.success();
    }
}
