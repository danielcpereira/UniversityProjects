import java.util.*;

public class MergeSort {
    public static void mergeSort(int[] arr, int l, int r) {
        if (l >= r) return;
        int mid = (l + r) / 2;
        mergeSort(arr, l, mid);
        mergeSort(arr, mid + 1, r);
        merge(arr, l, mid, r);
    }

    private static void merge(int[] arr, int l, int mid, int r) {
        int[] tmp = Arrays.copyOfRange(arr, l, r + 1);
        int i = 0, j = mid - l + 1, k = l;
        while (i <= mid - l && j <= r - l)
            arr[k++] = tmp[i] <= tmp[j] ? tmp[i++] : tmp[j++];
        while (i <= mid - l) arr[k++] = tmp[i++];
        while (j <= r - l)   arr[k++] = tmp[j++];
    }

    public static void main(String[] args) {
        int[] arr = {5, 2, 8, 1, 9, 3};
        mergeSort(arr, 0, arr.length - 1);
        System.out.println(Arrays.toString(arr));
    }
}