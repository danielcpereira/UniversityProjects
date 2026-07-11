class BugMix14 {
    static class Key { public int hashCode(){return 42;} } // Bug 1: Equals/HashCode
    public static void main(String[] args) {
        Key k = new Key();
        java.util.Map<Key,String> m = new java.util.HashMap<>();
        m.put(k, "v");
        int[] arr = new int[1];
        arr[100] = 1; // Bug 2: ArrayIndexOutOfBoundsException
        String s = null;
        System.out.println(s == null ? "ok" : s.length()); // Bug 3: NullPointer (potencial)
    }
}
