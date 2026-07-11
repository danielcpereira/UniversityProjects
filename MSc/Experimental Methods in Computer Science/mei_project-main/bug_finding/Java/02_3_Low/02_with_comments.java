class BugMix2 {
    public static void main(String[] args) {
        java.util.List<String> list = new java.util.ArrayList<>();
        list.add("a"); list.add("b");
        for (String s : list) {
            list.remove(s); // Bug 1: ConcurrentModificationException
        }
        Integer x = Integer.MAX_VALUE;
        x = x + 1; // Bug 2: Integer overflow silencioso
        Object[] objs = {new Object(), "str"};
        String str = (String) objs[0]; // Bug 3: ClassCastException
    }
}
