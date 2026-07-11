class BugMix11 {
    public static void main(String[] args) {
        String[] arr = new String[3];
        System.out.println(arr[3].length()); 
        int x = 1 << 31; 
        java.util.Set<Bad> set = new java.util.HashSet<>();
        set.add(new Bad()); 
    }
    static class Bad {
        public boolean equals(Object o) { return false; }
    }
}
