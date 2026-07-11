import java.util.concurrent.*;
import java.util.function.Consumer;

public class BackpressureStream {
    private final BlockingQueue<Integer> buffer;
    private final int batchSize;

    public BackpressureStream(int bufferSize, int batchSize) {
        this.buffer = new LinkedBlockingQueue<>(bufferSize);
        this.batchSize = batchSize;
    }

    public void produce(int[] data) throws InterruptedException {
        for (int item : data) {
            buffer.put(item);
            System.out.println("Produced: " + item + " | Buffer: " + buffer.size());
        }
    }

    public void consume(Consumer<Integer> handler) throws InterruptedException {
        int count = 0;
        while (count < batchSize) {
            Integer item = buffer.poll(200, TimeUnit.MILLISECONDS);
            if (item == null) break;
            handler.accept(item);
            count++;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BackpressureStream stream = new BackpressureStream(3, 5);
        Thread producer = new Thread(() -> {
            try { stream.produce(new int[]{1,2,3,4,5,6,7}); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        producer.start();
        Thread.sleep(100);
        stream.consume(item -> System.out.println("Consumed: " + item));
        producer.join();
    }
}
