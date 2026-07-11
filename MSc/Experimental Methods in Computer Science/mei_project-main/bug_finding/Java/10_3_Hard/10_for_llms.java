class BugMix10 {
    static java.util.List<Object> eternal = new java.util.ArrayList<>();
    static final Object L1 = new Object(), L2 = new Object();
    public static void main(String[] args) {
        eternal.add(new BugMix10()); 
        new Thread(() -> { synchronized(L1){synchronized(L2){}} }).start();
        new Thread(() -> { synchronized(L2){synchronized(L1){}} }).start(); 
        Object o = new int[5];
        String s = (String) o; 
    }
}
