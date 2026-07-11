class BugMix3 {
    static class BadKey {
        public boolean equals(Object o) { return true; }
    }
    public static void main(String[] args) {
        BadKey k = null;
        System.out.println(k.hashCode());
        int[] a = new int[3];
        a[-1] = 10; 
        java.util.Set<BadKey> set = new java.util.HashSet<>();
        set.add(new BadKey());
    }
}
