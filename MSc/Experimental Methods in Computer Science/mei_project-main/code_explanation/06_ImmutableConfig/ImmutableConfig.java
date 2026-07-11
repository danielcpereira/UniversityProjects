import java.util.Objects;

public class ImmutableConfig {
    private final String host;
    private final int port;
    private final int timeout;
    private final boolean ssl;

    private ImmutableConfig(Builder builder) {
        this.host = Objects.requireNonNull(builder.host, "host required");
        this.port = builder.port;
        this.timeout = builder.timeout;
        this.ssl = builder.ssl;
    }

    public String host() { return host; }
    public int port() { return port; }

    public ImmutableConfig withPort(int newPort) {
        return new Builder(this).port(newPort).build();
    }

    public static class Builder {
        private String host;
        private int port = 8080;
        private int timeout = 30;
        private boolean ssl = false;

        public Builder() {}
        public Builder(ImmutableConfig c) {
            this.host = c.host; this.port = c.port;
            this.timeout = c.timeout; this.ssl = c.ssl;
        }
        public Builder host(String h) { this.host = h; return this; }
        public Builder port(int p) { this.port = p; return this; }
        public Builder ssl(boolean s) { this.ssl = s; return this; }
        public ImmutableConfig build() { return new ImmutableConfig(this); }
    }

    public static void main(String[] args) {
        ImmutableConfig config = new ImmutableConfig.Builder()
            .host("localhost").port(9090).ssl(true).build();
        System.out.println(config.host() + ":" + config.port());

        ImmutableConfig updated = config.withPort(443);
        System.out.println(updated.host() + ":" + updated.port());
        System.out.println(config.port()); // 9090 — original inalterado
    }
}
