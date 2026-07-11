class BugMix1 {
    static java.util.List<Object> cache = new java.util.ArrayList<>(); 
    public static void main(String[] args) {
        String s = null;
        System.out.println(s.length()); 
        Object o = "string";
        Integer i = (Integer) o; 
        int[] arr = new int[5];
        System.out.println(arr[10]); 
        cache.add(new Object()); 
    }
}
