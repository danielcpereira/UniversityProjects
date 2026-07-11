class BugMix8 {
    static java.util.Map<BadKey, String> map = new java.util.HashMap<>();
    static class BadKey { public boolean equals(Object o){return true;} } 
    public static void main(String[] args) {
        map.put(new BadKey(), "val"); 
        Object[] objs = new Object[2];
        String s = (String) objs[5]; 
        String n = null;
        n.length(); 
    }
}
