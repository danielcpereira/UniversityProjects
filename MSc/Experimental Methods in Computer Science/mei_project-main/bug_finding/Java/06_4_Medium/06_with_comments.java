class BugMix6 {
    static class Bad {
        public int hashCode() { return 1; } // Bug 1: Equals/HashCode inconsistente (sem equals)
    }
    public static void main(String[] args) {
        Bad b = null;
        System.out.println(b.equals(null)); // Bug 2: NullPointerException
        int[] arr = {};
        System.out.println(arr[0]); // Bug 3: ArrayIndexOutOfBoundsException
        int sum = Integer.MAX_VALUE * 2; // Bug 4: Integer overflow
    }
}
