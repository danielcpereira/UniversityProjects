class BugMix5 {
    static java.util.List<Object> leak = new java.util.ArrayList<>();
    public static void main(String[] args) {
        leak.add(new Object()); 
        java.util.List<String> list = java.util.Arrays.asList("a");
        for (String s : list) list.add("b"); 
        Object o = 42;
        String str = (String) o; 
    }
}
