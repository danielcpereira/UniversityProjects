class BugMix3 {
    static class BadKey {
        public boolean equals(Object o) { return true; } // Bug 1: Equals/HashCode inconsistente
        // hashCode() não foi sobrescrito
    }
    public static void main(String[] args) {
        BadKey k = null;
        System.out.println(k.hashCode()); // Bug 2: NullPointerException
        int[] a = new int[3];
        a[-1] = 10; // Bug 3: ArrayIndexOutOfBoundsException
        java.util.Set<BadKey> set = new java.util.HashSet<>();
        set.add(new BadKey());
    }
}
