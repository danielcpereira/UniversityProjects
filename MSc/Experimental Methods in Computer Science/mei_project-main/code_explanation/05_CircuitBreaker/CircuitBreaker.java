public class CircuitBreaker {
    enum State { CLOSED, OPEN, HALF_OPEN }

    private State state = State.CLOSED;
    private int failures = 0;
    private long openedAt = 0;
    private final int threshold;
    private final long cooldownMs;

    public CircuitBreaker(int threshold, long cooldownMs) {
        this.threshold = threshold;
        this.cooldownMs = cooldownMs;
    }

    public String call(java.util.function.Supplier<String> action) {
        if (state == State.OPEN) {
            if (System.currentTimeMillis() - openedAt > cooldownMs)
                state = State.HALF_OPEN;
            else return "BLOCKED";
        }
        try {
            String result = action.get();
            if (state == State.HALF_OPEN) { state = State.CLOSED; failures = 0; }
            return result;
        } catch (Exception e) {
            failures++;
            if (failures >= threshold) { state = State.OPEN; openedAt = System.currentTimeMillis(); }
            return "FAILED: " + e.getMessage();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        CircuitBreaker cb = new CircuitBreaker(3, 500);
        for (int i = 0; i < 6; i++)
            System.out.println(cb.call(() -> { throw new RuntimeException("timeout"); }));
        Thread.sleep(600);
        System.out.println(cb.call(() -> "OK"));
    }
}
