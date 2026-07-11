class BugMix4 {
    static final Object lock1 = new Object();
    static final Object lock2 = new Object();
    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (lock1) {
                synchronized (lock2) {} // Bug 1: potencial Deadlock
            }
        }).start();
        new Thread(() -> {
            synchronized (lock2) {
                synchronized (lock1) {} // Bug 2: potencial Deadlock
            }
        }).start();
        String s = null;
        s.toString(); // Bug 3: NullPointerException
        int x = Integer.MAX_VALUE + 100; // Bug 4: Integer overflow
    }
}
