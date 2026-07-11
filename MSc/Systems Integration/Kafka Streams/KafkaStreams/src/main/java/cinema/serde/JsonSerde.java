package cinema.serde;

import com.google.gson.Gson;
import org.apache.kafka.common.serialization.Deserializer;
import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serializer;

import java.nio.charset.StandardCharsets;

/**
 * Generic JSON Serde backed by Gson.
 * Usage: new JsonSerde<>(MyClass.class)
 */
public class JsonSerde<T> implements Serde<T> {

    private static final Gson GSON = new Gson();
    private final Class<T> type;

    public JsonSerde(Class<T> type) {
        this.type = type;
    }

    @Override
    public Serializer<T> serializer() {
        return (topic, data) -> {
            if (data == null) return null;
            return GSON.toJson(data).getBytes(StandardCharsets.UTF_8);
        };
    }

    @Override
    public Deserializer<T> deserializer() {
        return (topic, bytes) -> {
            if (bytes == null) return null;
            return GSON.fromJson(new String(bytes, StandardCharsets.UTF_8), type);
        };
    }
}
