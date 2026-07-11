import java.util.*;

public class WriteAheadLog {
    private final List<String> log = new ArrayList<>();
    private final Map<String, String> store = new HashMap<>();
    private boolean committed = false;

    public void write(String key, String value) {
        if (committed) throw new IllegalStateException("Transaction already committed");
        log.add("SET " + key + "=" + value);
    }

    public void commit() {
        for (String entry : log) {
            String[] parts = entry.substring(4).split("=", 2);
            store.put(parts[0], parts[1]);
        }
        committed = true;
        log.clear();
    }

    public void rollback() {
        log.clear();
        committed = false;
    }

    public String read(String key) { return store.get(key); }

    public static void main(String[] args) {
        WriteAheadLog wal = new WriteAheadLog();
        wal.write("user", "Alice");
        wal.write("role", "admin");
        wal.commit();
        System.out.println(wal.read("user")); // Alice
        System.out.println(wal.read("role")); // admin

        WriteAheadLog wal2 = new WriteAheadLog();
        wal2.write("user", "Bob");
        wal2.rollback();
        System.out.println(wal2.read("user")); // null
    }
}
