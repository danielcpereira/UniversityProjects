public class ManualSemaphore {
    private int permits;

    public ManualSemaphore(int permits) { this.permits = permits; }

    public synchronized void acquire() throws InterruptedException {
        while (permits == 0) wait();
        permits--;
    }

    public synchronized void release() {
        permits++;
        notify();
    }

    public static void main(String[] args) {
        ManualSemaphore sem = new ManualSemaphore(2);
        Runnable task = () -> {
            try {
                sem.acquire();
                System.out.println(Thread.currentThread().getName() + " acquired");
                Thread.sleep(200);
                sem.release();
                System.out.println(Thread.currentThread().getName() + " released");
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        };
        for (int i = 0; i < 4; i++) new Thread(task, "T" + i).start();
    }
}
