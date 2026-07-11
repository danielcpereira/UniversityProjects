class BugMix7 {
    public static void main(String[] args) {
        Thread t1 = new Thread(() -> {
            synchronized (String.class) {
                synchronized (Integer.class) {}
            }
        });
        Thread t2 = new Thread(() -> {
            synchronized (Integer.class) {
                synchronized (String.class) {} 
            }
        });
        t1.start(); t2.start();
        java.util.List<Integer> l = new java.util.ArrayList<>();
        for (int i : l) l.remove(0);
    }
}
