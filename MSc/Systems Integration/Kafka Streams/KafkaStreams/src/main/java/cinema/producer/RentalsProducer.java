package cinema.producer;

import cinema.Topics;
import cinema.model.RentalEvent;
import cinema.model.RentalEvent.Duration;
import cinema.model.RentalEvent.Quality;
import cinema.model.RentalEvent.Type;
import com.google.gson.Gson;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.*;

/**
 * Simulates customers renting and buying films.
 * Publishes RentalEvent records to CinemaRentalsTopic.
 * Key = film title (ensures all events for a film go to the same partition).
 */
public class RentalsProducer {

    // Known films and their genres – mirrors the database seed data.
    private static final Map<String, String> FILMS = new LinkedHashMap<>();
    static {
        FILMS.put("Galactic Odyssey",  "Science Fiction");
        FILMS.put("Shadow Protocol",   "Thriller");
        FILMS.put("Laugh Factory",     "Comedy");
        FILMS.put("The Last Frontier", "Action");
        FILMS.put("Silent Waters",     "Drama");
        FILMS.put("Night Crawler",     "Horror");
        FILMS.put("Tiny Heroes",       "Animation");
        FILMS.put("Planet in Peril",   "Documentary");
    }

    // Rental price matrix: quality × duration → multiplier applied to base €2.99
    private static final double BASE_RENTAL = 2.99;
    private static final double[][] RENTAL_PRICE = {
        // ONE_DAY  TWO_DAYS  ONE_WEEK
        { 1.0,     1.7,      3.5 },   // HD
        { 1.4,     2.2,      4.5 },   // FULL_HD
        { 2.0,     3.2,      6.5 },   // UHD_4K
    };

    // Purchase prices – mirrors DB seed data
    private static final Map<String, Double> BUY_PRICE = new LinkedHashMap<>();
    static {
        BUY_PRICE.put("Galactic Odyssey",  14.99);
        BUY_PRICE.put("Shadow Protocol",   12.99);
        BUY_PRICE.put("Laugh Factory",      9.99);
        BUY_PRICE.put("The Last Frontier", 11.99);
        BUY_PRICE.put("Silent Waters",     13.99);
        BUY_PRICE.put("Night Crawler",     10.99);
        BUY_PRICE.put("Tiny Heroes",        8.99);
        BUY_PRICE.put("Planet in Peril",   12.49);
    }

    public static void main(String[] args) throws InterruptedException {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "broker1:9092,broker2:9092,broker3:9092");
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,   StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        // Exactly-once semantics
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        props.put(ProducerConfig.ACKS_CONFIG, "all");

        Gson gson = new Gson();
        Random rnd = new Random();
        List<String> filmList = new ArrayList<>(FILMS.keySet());

        System.out.println("▶ RentalsProducer started. Publishing to " + Topics.RENTALS);

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {
            while (true) {
                String film  = filmList.get(rnd.nextInt(filmList.size()));
                String genre = FILMS.get(film);

                // 30 % chance of BUY, 70 % chance of RENT
                Type type = rnd.nextDouble() < 0.30 ? Type.BUY : Type.RENT;

                Quality  quality  = Quality.values()[rnd.nextInt(Quality.values().length)];
                Duration duration = Duration.values()[rnd.nextInt(Duration.values().length)];

                double amount;
                if (type == Type.BUY) {
                    amount = BUY_PRICE.get(film);
                } else {
                    amount = BASE_RENTAL * RENTAL_PRICE[quality.ordinal()][duration.ordinal()];
                    amount = Math.round(amount * 100.0) / 100.0;
                }

                RentalEvent event = new RentalEvent(
                        film, genre, type, quality, duration,
                        amount, System.currentTimeMillis());

                ProducerRecord<String, String> record =
                        new ProducerRecord<>(Topics.RENTALS, film, gson.toJson(event));

                producer.send(record, (meta, ex) -> {
                    if (ex != null) {
                        System.err.println("Error sending rental: " + ex.getMessage());
                    } else {
                        System.out.printf("  → Rental: partition=%d offset=%d | %s%n",
                                meta.partition(), meta.offset(), event);
                    }
                });

                // Publish between 1 and 4 events per second
                Thread.sleep(250 + rnd.nextInt(750));
            }
        }
    }
}
