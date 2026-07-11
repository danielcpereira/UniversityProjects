class BugMix5 {
    static java.util.List<Object> leak = new java.util.ArrayList<>();
    public static void main(String[] args) {
        leak.add(new Object()); // Bug 1: Memory Leak
        java.util.List<String> list = java.util.Arrays.asList("a");
        for (String s : list) list.add("b"); // Bug 2: ConcurrentModificationException
        Object o = 42;
        String str = (String) o; // Bug 3: ClassCastException
    }
}
