package cinema.producer;

import cinema.Topics;
import cinema.model.LicensingEvent;
import com.google.gson.Gson;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.*;

/**
 * Simulates the platform paying licensing fees to studios.
 * Publishes LicensingEvent records to CinemaLicensingTopic.
 * Key = film title (mirrors RentalsProducer partitioning for clean joins).
 */
public class LicensingProducer {

    private static final Map<String, String> FILM_STUDIO = new LinkedHashMap<>();
    static {
        FILM_STUDIO.put("Galactic Odyssey",  "StarVision Studios");
        FILM_STUDIO.put("Shadow Protocol",   "DarkFrame Productions");
        FILM_STUDIO.put("Laugh Factory",     "Comedy Central Films");
        FILM_STUDIO.put("The Last Frontier", "Epic Pictures");
        FILM_STUDIO.put("Silent Waters",     "Arthouse International");
        FILM_STUDIO.put("Night Crawler",     "Fear Factor Films");
        FILM_STUDIO.put("Tiny Heroes",       "KidWorld Animation");
        FILM_STUDIO.put("Planet in Peril",   "EarthWatch Docs");
    }

    // Base licensing fee per event (simulates periodic royalty payment)
    private static final Map<String, Double> BASE_FEE = new LinkedHashMap<>();
    static {
        BASE_FEE.put("Galactic Odyssey",  4.50);
        BASE_FEE.put("Shadow Protocol",   3.80);
        BASE_FEE.put("Laugh Factory",     2.90);
        BASE_FEE.put("The Last Frontier", 3.20);
        BASE_FEE.put("Silent Waters",     4.10);
        BASE_FEE.put("Night Crawler",     3.00);
        BASE_FEE.put("Tiny Heroes",       2.50);
        BASE_FEE.put("Planet in Peril",   3.60);
    }

    public static void main(String[] args) throws InterruptedException {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "broker1:9092,broker2:9092,broker3:9092");
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,   StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        props.put(ProducerConfig.ACKS_CONFIG, "all");

        Gson gson = new Gson();
        Random rnd = new Random();
        List<String> filmList = new ArrayList<>(FILM_STUDIO.keySet());

        System.out.println("▶ LicensingProducer started. Publishing to " + Topics.LICENSING);

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {
            while (true) {
                String film   = filmList.get(rnd.nextInt(filmList.size()));
                String studio = FILM_STUDIO.get(film);

                // Small random variation around base fee (±20%)
                double base   = BASE_FEE.get(film);
                double amount = base * (0.80 + rnd.nextDouble() * 0.40);
                amount        = Math.round(amount * 100.0) / 100.0;

                LicensingEvent event = new LicensingEvent(
                        film, studio, amount, System.currentTimeMillis());

                ProducerRecord<String, String> record =
                        new ProducerRecord<>(Topics.LICENSING, film, gson.toJson(event));

                producer.send(record, (meta, ex) -> {
                    if (ex != null) {
                        System.err.println("Error sending licensing: " + ex.getMessage());
                    } else {
                        System.out.printf("  → License: partition=%d offset=%d | %s%n",
                                meta.partition(), meta.offset(), event);
                    }
                });

                // Licensing fees arrive less frequently than rentals (~every 1-3 s)
                Thread.sleep(1000 + rnd.nextInt(2000));
            }
        }
    }
}
