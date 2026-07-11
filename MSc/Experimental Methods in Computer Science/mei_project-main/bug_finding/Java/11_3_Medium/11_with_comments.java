class BugMix11 {
    public static void main(String[] args) {
        String[] arr = new String[3];
        System.out.println(arr[3].length()); // Bug 1: ArrayIndex + NullPointer (em cadeia)
        int x = 1 << 31; // Bug 2: Integer overflow (comportamento silencioso)
        java.util.Set<Bad> set = new java.util.HashSet<>();
        set.add(new Bad()); // Bug 3: Equals/HashCode inconsistente
    }
    static class Bad {
        public boolean equals(Object o) { return false; }
        // hashCode default inconsistente em alguns casos
    }
}
