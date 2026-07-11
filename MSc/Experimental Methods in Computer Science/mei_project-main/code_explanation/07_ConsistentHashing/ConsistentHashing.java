import java.util.*;

public class ConsistentHashing {
    private final TreeMap<Integer, String> ring = new TreeMap<>();
    private final int virtualNodes;

    public ConsistentHashing(int virtualNodes) {
        this.virtualNodes = virtualNodes;
    }

    public void addNode(String node) {
        for (int i = 0; i < virtualNodes; i++)
            ring.put((node + "#" + i).hashCode(), node);
    }

    public void removeNode(String node) {
        for (int i = 0; i < virtualNodes; i++)
            ring.remove((node + "#" + i).hashCode());
    }

    public String getNode(String key) {
        if (ring.isEmpty()) return null;
        int hash = key.hashCode();
        Map.Entry<Integer, String> entry = ring.ceilingEntry(hash);
        return (entry != null ? entry : ring.firstEntry()).getValue();
    }

    public static void main(String[] args) {
        ConsistentHashing ch = new ConsistentHashing(3);
        ch.addNode("ServerA"); ch.addNode("ServerB"); ch.addNode("ServerC");
        System.out.println(ch.getNode("user1"));
        System.out.println(ch.getNode("user2"));
        ch.removeNode("ServerB");
        System.out.println(ch.getNode("user1"));
    }
}
