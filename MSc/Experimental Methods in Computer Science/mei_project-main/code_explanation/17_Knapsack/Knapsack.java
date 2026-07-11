public class Knapsack {
    public static int knapsack(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];
        for (int i = 1; i <= n; i++)
            for (int w = 0; w <= capacity; w++) {
                dp[i][w] = dp[i-1][w];
                if (weights[i-1] <= w)
                    dp[i][w] = Math.max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1]);
            }
        return dp[n][capacity];
    }

    public static void main(String[] args) {
        int[] w = {1, 3, 4, 5}, v = {1, 4, 5, 7};
        System.out.println(knapsack(w, v, 7));  
        System.out.println(knapsack(w, v, 10)); 
    }
}