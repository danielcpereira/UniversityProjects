package cinema.streams;

import cinema.Topics;
import cinema.model.AggregateAvg;
import cinema.model.LicensingEvent;
import cinema.model.RentalEvent;
import cinema.model.TopEntry;
import cinema.serde.JsonSerde;
import com.google.gson.Gson;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.kstream.*;

import java.time.Duration;
import java.util.Properties;

/**
 * CinemaStreamsApp – implements all 17 project requirements using Kafka Streams.
 *
 * Req  1-4  → handled by REST/CLI (DB ops, not Streams)
 * Req  5    → revenue per film          : reduce()
 * Req  6    → expenses per film         : reduce()
 * Req  7    → profit per film           : join()
 * Req  8    → total revenue             : groupBy() + reduce()
 * Req  9    → total expenses            : groupBy() + reduce()
 * Req  10   → total profit              : join()
 * Req  11   → avg transaction per film  : aggregate()
 * Req  12   → avg transaction all films : groupBy() + aggregate()
 * Req  13   → film with highest profit  : aggregate() with historical TopEntry
 * Req  14   → revenue last hour         : tumbling window
 * Req  15   → expenses last hour        : tumbling window
 * Req  16   → profit last hour          : join() + tumbling window
 * Req  17   → top genre per film        : aggregate() + TopEntry
 */
public class CinemaStreamsApp {

    private static final Gson GSON = new Gson();

    // ── Serdes ────────────────────────────────────────────────────────────────
    private static final JsonSerde<RentalEvent>   RENTAL_SERDE    = new JsonSerde<>(RentalEvent.class);
    private static final JsonSerde<LicensingEvent> LICENSE_SERDE  = new JsonSerde<>(LicensingEvent.class);
    private static final JsonSerde<AggregateAvg>  AVG_SERDE       = new JsonSerde<>(AggregateAvg.class);
    private static final JsonSerde<TopEntry>      TOP_SERDE       = new JsonSerde<>(TopEntry.class);

    // Sink schema wrapper – Kafka Connect JSON sink requires {"schema":…,"payload":…}
    // We use auto.create=true with schema inference via JsonConverter with schemas.enable=true.
    // For simplicity each output topic carries a plain double or JSON string value
    // and we rely on the sink connector's auto-schema detection.

    public static void main(String[] args) {
        Properties props = buildProperties();
        Topology topology = buildTopology();

        System.out.println(topology.describe());

        KafkaStreams streams = new KafkaStreams(topology, props);

        // Clean shutdown
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));

        streams.start();
        System.out.println("▶ CinemaStreamsApp running…");
    }

    // ─────────────────────────────────────────────────────────────────────────
    static Topology buildTopology() {
        StreamsBuilder builder = new StreamsBuilder();

        // ── Source streams ────────────────────────────────────────────────────

        // All rentals (key = film title)
        KStream<String, RentalEvent> rentals = builder.stream(
                Topics.RENTALS,
                Consumed.with(Serdes.String(), RENTAL_SERDE));

        // All licensing fees (key = film title)
        KStream<String, LicensingEvent> licensing = builder.stream(
                Topics.LICENSING,
                Consumed.with(Serdes.String(), LICENSE_SERDE));

        // ── KTables for aggregating totals (keyed by film title) ──────────────

        // REQ 5 – Revenue per film (reduce)
        KTable<String, Double> revenuePerFilm = rentals
                .mapValues(RentalEvent::getAmount)
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .reduce(Double::sum,
                        Materialized.with(Serdes.String(), Serdes.Double()));

        toDoubleOutputTopic(revenuePerFilm, Topics.OUT_REVENUE_PER_FILM, "revenue");

        // REQ 6 – Expenses per film (reduce)
        KTable<String, Double> expensesPerFilm = licensing
                .mapValues(LicensingEvent::getAmount)
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .reduce(Double::sum,
                        Materialized.with(Serdes.String(), Serdes.Double()));

        toDoubleOutputTopic(expensesPerFilm, Topics.OUT_EXPENSES_PER_FILM, "expenses");

        // REQ 7 – Profit per film (join of two KTables)
        KTable<String, Double> profitPerFilm = revenuePerFilm
                .join(expensesPerFilm,
                      (revenue, expense) -> revenue - expense,
                      Materialized.with(Serdes.String(), Serdes.Double()));

        toDoubleOutputTopic(profitPerFilm, Topics.OUT_PROFIT_PER_FILM, "profit");

        // REQ 8 – Total revenue across all films (groupBy to single key)
        KTable<String, Double> totalRevenue = rentals
                .mapValues(RentalEvent::getAmount)
                .groupBy((film, amount) -> "TOTAL",
                         Grouped.with(Serdes.String(), Serdes.Double()))
                .reduce(Double::sum,
                        Materialized.with(Serdes.String(), Serdes.Double()));

        toDoubleOutputTopic(totalRevenue, Topics.OUT_TOTAL_REVENUE, "revenue");

        // REQ 9 – Total expenses across all films
        KTable<String, Double> totalExpenses = licensing
                .mapValues(LicensingEvent::getAmount)
                .groupBy((film, amount) -> "TOTAL",
                         Grouped.with(Serdes.String(), Serdes.Double()))
                .reduce(Double::sum,
                        Materialized.with(Serdes.String(), Serdes.Double()));

        toDoubleOutputTopic(totalExpenses, Topics.OUT_TOTAL_EXPENSES, "expenses");

        // REQ 10 – Total profit (join of total KTables)
        KTable<String, Double> totalProfit = totalRevenue
                .join(totalExpenses,
                      (rev, exp) -> rev - exp,
                      Materialized.with(Serdes.String(), Serdes.Double()));

        toDoubleOutputTopic(totalProfit, Topics.OUT_TOTAL_PROFIT, "profit");

        // REQ 11 – Average transaction amount per film (aggregate)
        KTable<String, AggregateAvg> avgPerFilm = rentals
                .mapValues(RentalEvent::getAmount)
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .aggregate(
                        AggregateAvg::new,
                        (film, amount, agg) -> agg.add(amount),
                        Materialized.with(Serdes.String(), AVG_SERDE));

        avgPerFilm.toStream()
                .mapValues((film, agg) -> buildAvgJson(film, agg))
                .to(Topics.OUT_AVG_TRANSACTION_FILM,
                    Produced.with(Serdes.String(), Serdes.String()));

        // REQ 12 – Average transaction amount across all films (groupBy + aggregate)
        KTable<String, AggregateAvg> avgAllFilms = rentals
                .mapValues(RentalEvent::getAmount)
                .groupBy((film, amount) -> "ALL",
                         Grouped.with(Serdes.String(), Serdes.Double()))
                .aggregate(
                        AggregateAvg::new,
                        (k, amount, agg) -> agg.add(amount),
                        Materialized.with(Serdes.String(), AVG_SERDE));

        avgAllFilms.toStream()
                .mapValues((k, agg) -> buildAvgJson(k, agg))
                .to(Topics.OUT_AVG_TRANSACTION_ALL,
                    Produced.with(Serdes.String(), Serdes.String()));

        // REQ 13 – Film with highest profit
        profitPerFilm.toStream()
                .map((film, profit) -> new KeyValue<>("TOP", film + "|||" + profit))
                .groupByKey(Grouped.with(Serdes.String(), Serdes.String()))
                .reduce((existing, newVal) -> {
                    double existingProfit = Double.parseDouble(existing.split("\\|\\|\\|")[1]);
                    double newProfit = Double.parseDouble(newVal.split("\\|\\|\\|")[1]);
                    return newProfit > existingProfit ? newVal : existing;
                }, Materialized.with(Serdes.String(), Serdes.String()))
                .toStream()
                .mapValues((k, val) -> {
                    String[] parts = val.split("\\|\\|\\|");
                    String filmTitle = parts[0];
                    double profit = Double.parseDouble(parts[1]);
                    return buildTopJson(new TopEntry(filmTitle, profit), "film_title", "profit");
                })
                .to(Topics.OUT_HIGHEST_PROFIT_FILM,
                    Produced.with(Serdes.String(), Serdes.String()));

        // ── Tumbling time windows (1 hour) ────────────────────────────────────
        Duration windowSize = Duration.ofHours(1);

        // REQ 14 – Revenue in last hour
        KTable<Windowed<String>, Double> revenueWindow = rentals
                .mapValues(RentalEvent::getAmount)
                .groupBy((film, amount) -> "TOTAL",
                         Grouped.with(Serdes.String(), Serdes.Double()))
                .windowedBy(TimeWindows.ofSizeWithNoGrace(windowSize))
                .reduce(Double::sum);

        revenueWindow.toStream()
                .map((wk, v) -> new KeyValue<>(windowKey(wk), buildWindowJson("revenue", v)))
                .to(Topics.OUT_REVENUE_LAST_HOUR, Produced.with(Serdes.String(), Serdes.String()));

        // REQ 15 – Expenses in last hour
        KTable<Windowed<String>, Double> expensesWindow = licensing
                .mapValues(LicensingEvent::getAmount)
                .groupBy((film, amount) -> "TOTAL",
                         Grouped.with(Serdes.String(), Serdes.Double()))
                .windowedBy(TimeWindows.ofSizeWithNoGrace(windowSize))
                .reduce(Double::sum);

        expensesWindow.toStream()
                .map((wk, v) -> new KeyValue<>(windowKey(wk), buildWindowJson("expenses", v)))
                .to(Topics.OUT_EXPENSES_LAST_HOUR, Produced.with(Serdes.String(), Serdes.String()));

        // REQ 16 – Profit in last hour (join the two windowed tables)
        KTable<Windowed<String>, Double> profitWindow = revenueWindow
                .join(expensesWindow,
                      (rev, exp) -> rev - exp);

        profitWindow.toStream()
                .map((wk, v) -> new KeyValue<>(windowKey(wk), buildWindowJson("profit", v)))
                .to(Topics.OUT_PROFIT_LAST_HOUR, Produced.with(Serdes.String(), Serdes.String()));

        // REQ 17 – Top genre by revenue per film
        // Key = film title, we aggregate per (film, genre) pair then pick the max genre
        rentals
                .groupByKey(Grouped.with(Serdes.String(), RENTAL_SERDE))
                .aggregate(
                        () -> new TopEntry("", 0.0),
                        (film, event, top) -> top.update(event.getGenre(), top.getValue() + event.getAmount()),
                        Materialized.with(Serdes.String(), TOP_SERDE))
                .toStream()
                .mapValues((film, top) -> buildTopGenreJson(film, top))
                .to(Topics.OUT_TOP_GENRE_PER_FILM, Produced.with(Serdes.String(), Serdes.String()));

        return builder.build();
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    /**
     * Converts a KTable<String, Double> to an output topic with Connect-compatible JSON.
     * Schema: {"schema":{"type":"struct","fields":[{"field":"id","type":"string"},{"field":"<valueField>","type":"double"}]},"payload":{"id":"<key>","<valueField>":<value>}}
     */
    private static void toDoubleOutputTopic(KTable<String, Double> table,
                                            String topic, String valueField) {
        table.toStream()
                .mapValues((key, value) -> buildDoubleJson(key, valueField, value))
                .to(topic, Produced.with(Serdes.String(), Serdes.String()));
    }

    private static String buildDoubleJson(String id, String field, double value) {
        return String.format(
                "{\"schema\":{\"type\":\"struct\",\"fields\":[{\"field\":\"id\",\"type\":\"string\",\"optional\":false},{\"field\":\"%s\",\"type\":\"double\",\"optional\":true}],\"optional\":false},\"payload\":{\"id\":\"%s\",\"%s\":%.4f}}",
                field, id, field, value);
    }

    private static String buildAvgJson(String id, AggregateAvg agg) {
        return String.format(
                "{\"schema\":{\"type\":\"struct\",\"fields\":[{\"field\":\"id\",\"type\":\"string\",\"optional\":false},{\"field\":\"avg_value\",\"type\":\"double\",\"optional\":true},{\"field\":\"count\",\"type\":\"int64\",\"optional\":true}],\"optional\":false},\"payload\":{\"id\":\"%s\",\"avg_value\":%.4f,\"count\":%d}}",
                id, agg.getAvg(), agg.getCount());
    }

    private static String buildTopJson(TopEntry top, String labelField, String valueField) {
        return String.format(
                "{\"schema\":{\"type\":\"struct\",\"fields\":[{\"field\":\"id\",\"type\":\"string\",\"optional\":false},{\"field\":\"%s\",\"type\":\"string\",\"optional\":true},{\"field\":\"%s\",\"type\":\"double\",\"optional\":true}],\"optional\":false},\"payload\":{\"id\":\"TOP\",\"%s\":\"%s\",\"%s\":%.4f}}",
                labelField, valueField, labelField, top.getLabel(), valueField, top.getValue());
    }

    private static String buildTopGenreJson(String filmTitle, TopEntry top) {
        return String.format(
                "{\"schema\":{\"type\":\"struct\",\"fields\":[{\"field\":\"id\",\"type\":\"string\",\"optional\":false},{\"field\":\"genre_name\",\"type\":\"string\",\"optional\":true},{\"field\":\"revenue\",\"type\":\"double\",\"optional\":true}],\"optional\":false},\"payload\":{\"id\":\"%s\",\"genre_name\":\"%s\",\"revenue\":%.4f}}",
                filmTitle, top.getLabel(), top.getValue());
    }

    private static String buildWindowJson(String field, double value) {
        return String.format(
                "{\"schema\":{\"type\":\"struct\",\"fields\":[{\"field\":\"id\",\"type\":\"string\",\"optional\":false},{\"field\":\"%s\",\"type\":\"double\",\"optional\":true}],\"optional\":false},\"payload\":{\"id\":\"TOTAL\",\"%s\":%.4f}}",
                field, field, value);
    }

    private static String windowKey(Windowed<String> wk) {
        return wk.key() + "_" + wk.window().startTime().toEpochMilli();
    }

    private static Properties buildProperties() {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG,
                  "cinema-streaming-app");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG,
                  "broker1:9092,broker2:9092,broker3:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG,
                  Serdes.String().getClass().getName());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG,
                  Serdes.String().getClass().getName());
        // Exactly-once processing
        props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG,
                  StreamsConfig.EXACTLY_ONCE_V2);
        // Commit every 1 second for demo responsiveness
        props.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, 1000);
        return props;
    }
}