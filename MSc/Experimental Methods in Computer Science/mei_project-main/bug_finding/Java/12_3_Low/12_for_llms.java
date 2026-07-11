class BugMix12 {
    static java.util.List<String> shared = new java.util.ArrayList<>();
    public static void main(String[] args) {
        shared.add("leak"); 
        Object obj = "texto";
        Integer num = (Integer) obj; 
        for (int i = Integer.MAX_VALUE - 5; i < Integer.MAX_VALUE + 10; i++) {} 
    }
}
