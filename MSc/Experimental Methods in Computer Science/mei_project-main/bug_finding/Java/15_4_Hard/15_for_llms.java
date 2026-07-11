class BugMix15 {
    static final Object A = new Object(), B = new Object();
    static java.util.List<Object> cache = new java.util.ArrayList<>();
    public static void main(String[] args) {
        cache.add(new Object()); 
        new Thread(() -> {synchronized(A){try{Thread.sleep(10);}catch(Exception e){} synchronized(B){}}}).start();
        new Thread(() -> {synchronized(B){synchronized(A){}}}).start(); 
        Integer max = Integer.MAX_VALUE;
        max = max + Integer.MAX_VALUE; 
        Object wrong = "str";
        int x = (int) wrong; 
    }
}
