class BugMix6 {
    static class Bad {
        public int hashCode() { return 1; } 
    }
    public static void main(String[] args) {
        Bad b = null;
        System.out.println(b.equals(null)); 
        int[] arr = {};
        System.out.println(arr[0]); 
        int sum = Integer.MAX_VALUE * 2; 
    }
}
