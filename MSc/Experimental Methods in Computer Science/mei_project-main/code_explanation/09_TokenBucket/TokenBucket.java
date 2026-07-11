public class TokenBucket {
    private final int capacity;
    private final double refillRate;
    private double tokens;
    private long lastRefill;

    public TokenBucket(int capacity, double refillRate) {
        this.capacity = capacity;
        this.refillRate = refillRate;
        this.tokens = capacity;
        this.lastRefill = System.nanoTime();
    }

    public synchronized boolean consume(int requested) {
        refill();
        if (tokens >= requested) {
            tokens -= requested;
            return true;
        }
        return false;
    }

    private void refill() {
        long now = System.nanoTime();
        double elapsed = (now - lastRefill) / 1_000_000_000.0;
        tokens = Math.min(capacity, tokens + elapsed * refillRate);
        lastRefill = now;
    }

    public static void main(String[] args) throws InterruptedException {
        TokenBucket tb = new TokenBucket(10, 2.0);
        for (int i = 0; i < 6; i++) {
            System.out.println("Request " + i + ": " + tb.consume(3));
            Thread.sleep(500);
        }
    }
}
