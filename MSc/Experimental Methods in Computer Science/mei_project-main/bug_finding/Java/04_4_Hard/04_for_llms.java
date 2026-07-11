class BugMix4 {
    static final Object lock1 = new Object();
    static final Object lock2 = new Object();
    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (lock1) {
                synchronized (lock2) {} 
            }
        }).start();
        new Thread(() -> {
            synchronized (lock2) {
                synchronized (lock1) {} 
            }
        }).start();
        String s = null;
        s.toString(); 
        int x = Integer.MAX_VALUE + 100; 
    }
}
