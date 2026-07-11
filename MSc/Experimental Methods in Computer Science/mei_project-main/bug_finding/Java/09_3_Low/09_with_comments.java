class BugMix9 {
    public static void main(String[] args) {
        int[] arr = new int[10];
        for (int i = 0; i < 20; i++) arr[i] = i; // Bug 1: ArrayIndexOutOfBoundsException
        Integer big = Integer.MAX_VALUE;
        big += 5000; // Bug 2: Integer overflow
        java.util.List<String> list = new java.util.ArrayList<>(java.util.Arrays.asList("a"));
        list.removeIf(s -> true);
        for (String s : list) System.out.println(s); // Bug 3: ConcurrentModificationException
    }
}
