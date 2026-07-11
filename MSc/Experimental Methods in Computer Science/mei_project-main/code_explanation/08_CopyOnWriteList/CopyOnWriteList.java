import java.util.*;
import java.util.concurrent.locks.*;

public class CopyOnWriteList<T> {
    private volatile List<T> inner = new ArrayList<>();
    private final ReentrantLock lock = new ReentrantLock();

    public void add(T item) {
        lock.lock();
        try {
            List<T> copy = new ArrayList<>(inner);
            copy.add(item);
            inner = copy;
        } finally {
            lock.unlock();
        }
    }

    public T get(int index) { return inner.get(index); }
    public int size() { return inner.size(); }

    public static void main(String[] args) throws InterruptedException {
        CopyOnWriteList<Integer> list = new CopyOnWriteList<>();
        Thread writer = new Thread(() -> {
            for (int i = 0; i < 5; i++) list.add(i);
        });
        Thread reader = new Thread(() -> {
            for (int i = 0; i < 5; i++)
                System.out.println("size=" + list.size());
        });
        writer.start(); reader.start();
        writer.join(); reader.join();
        System.out.println("Final size: " + list.size());
    }
}
