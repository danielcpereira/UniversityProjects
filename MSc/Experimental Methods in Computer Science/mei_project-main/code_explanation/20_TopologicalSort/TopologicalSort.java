import java.util.*;

public class TopologicalSort {
    public static List<Integer> topoSort(int n, List<List<Integer>> adj) {
        int[] inDegree = new int[n];
        for (List<Integer> neighbors : adj)
            for (int v : neighbors) inDegree[v]++;
        Queue<Integer> q = new LinkedList<>();
        for (int i = 0; i < n; i++) if (inDegree[i] == 0) q.add(i);
        List<Integer> order = new ArrayList<>();
        while (!q.isEmpty()) {
            int u = q.poll(); order.add(u);
            for (int v : adj.get(u)) if (--inDegree[v] == 0) q.add(v);
        }
        return order.size() == n ? order : List.of(); 
    }

    public static void main(String[] args) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < 6; i++) adj.add(new ArrayList<>());
        adj.get(5).add(2); adj.get(5).add(0); adj.get(4).add(0);
        adj.get(4).add(1); adj.get(2).add(3); adj.get(3).add(1);
        System.out.println(topoSort(6, adj)); 
    }
}