class BugMix2 {
    public static void main(String[] args) {
        java.util.List<String> list = new java.util.ArrayList<>();
        list.add("a"); list.add("b");
        for (String s : list) {
            list.remove(s);
        }
        Integer x = Integer.MAX_VALUE;
        x = x + 1;
        Object[] objs = {new Object(), "str"};
        String str = (String) objs[0];
    }
}
