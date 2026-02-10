package com.googol.meta1;

import java.io.Serializable;

public class BarrelStats implements Serializable {
    private final int indexSize;
    private final double avgResponseTime; // seconds
    private final boolean busy;

    public BarrelStats(int indexSize, double avgResponseTime, boolean busy) {
        this.indexSize = indexSize;
        this.avgResponseTime = avgResponseTime;
        this.busy = busy;
    }

    public int getIndexSize() {
        return indexSize;
    }

    public double getAvgResponseTime() {
        return avgResponseTime;
    }

    public boolean isBusy() {
        return busy;
    }
}
