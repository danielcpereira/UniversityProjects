import java.util.*;

public class SlidingWindowMax {
    public static int[] maxSlidingWindow(int[] nums, int k) {
        int n = nums.length;
        int[] result = new int[n - k + 1];
        Deque<Integer> deque = new ArrayDeque<>();

        for (int i = 0; i < n; i++) {
            while (!deque.isEmpty() && deque.peekFirst() < i - k + 1)
                deque.pollFirst();
            while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i])
                deque.pollLast();
            deque.addLast(i);
            if (i >= k - 1)
                result[i - k + 1] = nums[deque.peekFirst()];
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println(Arrays.toString(maxSlidingWindow(nums, 3)));
        // [3, 3, 5, 5, 6, 7]

        int[] nums2 = {4, 3, 11, 2, 9};
        System.out.println(Arrays.toString(maxSlidingWindow(nums2, 2)));
        // [4, 11, 11, 9]
    }
}
