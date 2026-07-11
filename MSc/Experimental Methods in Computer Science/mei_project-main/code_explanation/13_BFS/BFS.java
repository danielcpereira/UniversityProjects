import java.util.*;

public class BFS {
    public static List<Integer> bfs(Map<Integer, List<Integer>> graph, int start) {
        List<Integer> order = new ArrayList<>();
        Set<Integer> visited = new HashSet<>();
        Queue<Integer> queue = new LinkedList<>();
        queue.add(start);
        visited.add(start);
        while (!queue.isEmpty()) {
            int node = queue.poll();
            order.add(node);
            for (int neighbor : graph.getOrDefault(node, List.of()))
                if (visited.add(neighbor)) queue.add(neighbor);
        }
        return order;
    }

    public static void main(String[] args) {
        Map<Integer, List<Integer>> g = new HashMap<>();
        g.put(1, List.of(2, 3)); g.put(2, List.of(4, 5)); g.put(3, List.of(6));
        System.out.println(bfs(g, 1)); 
    }
}