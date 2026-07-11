import java.util.BitSet;

public class BloomFilter {
    private final BitSet bits;
    private final int size;
    private final int[] seeds = {7, 11, 31};

    public BloomFilter(int size) {
        this.size = size;
        this.bits = new BitSet(size);
    }

    private int hash(String val, int seed) {
        int h = 0;
        for (char c : val.toCharArray()) h = h * seed + c;
        return Math.abs(h % size);
    }

    public void add(String val) {
        for (int seed : seeds) bits.set(hash(val, seed));
    }

    public boolean mightContain(String val) {
        for (int seed : seeds) if (!bits.get(hash(val, seed))) return false;
        return true;
    }

    public static void main(String[] args) {
        BloomFilter bf = new BloomFilter(1000);
        bf.add("apple"); bf.add("banana");
        System.out.println(bf.mightContain("apple"));   // true
        System.out.println(bf.mightContain("banana"));  // true
        System.out.println(bf.mightContain("cherry"));  // false (provavelmente)
    }
}
