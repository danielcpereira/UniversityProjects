class BugMix13 {
    public static void main(String[] args) {
        java.util.List<Integer> list = new java.util.ArrayList<>();
        list.add(1);
        java.util.Iterator<Integer> it = list.iterator();
        while (it.hasNext()) {
            list.add(2); 
        }
        int[] a = null;
        int val = a[0]; 
        Object o = a;
        int[] b = (int[]) o; 
    }
}
