class BugMix1 {
    static java.util.List<Object> cache = new java.util.ArrayList<>(); // Bug Memory Leak
    public static void main(String[] args) {
        String s = null;
        System.out.println(s.length()); // Bug 1: NullPointerException
        Object o = "string";
        Integer i = (Integer) o; // Bug 2: ClassCastException
        int[] arr = new int[5];
        System.out.println(arr[10]); // Bug 3: ArrayIndexOutOfBoundsException
        cache.add(new Object()); // Mantém referência forever
    }
}
