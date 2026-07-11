class BugMix14 {
    static class Key { public int hashCode(){return 42;} } 
    public static void main(String[] args) {
        Key k = new Key();
        java.util.Map<Key,String> m = new java.util.HashMap<>();
        m.put(k, "v");
        int[] arr = new int[1];
        arr[100] = 1; 
        String s = null;
        System.out.println(s == null ? "ok" : s.length()); 
    }
}
