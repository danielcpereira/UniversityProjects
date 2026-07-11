class BugMix8 {
    static java.util.Map<BadKey, String> map = new java.util.HashMap<>();
    static class BadKey { public boolean equals(Object o){return true;} } // Bug 1: Equals/HashCode
    public static void main(String[] args) {
        map.put(new BadKey(), "val"); // Problemas em HashMap
        Object[] objs = new Object[2];
        String s = (String) objs[5]; // Bug 2: ArrayIndexOutOfBounds + ClassCast
        String n = null;
        n.length(); // Bug 3: NullPointerException
    }
}
