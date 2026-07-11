package cinema;

/** Central registry of all Kafka topic names used in the Cinema Streaming platform. */
public final class Topics {

    private Topics() {}

    // ── Input topics ──────────────────────────────────────────────────────────
    /** Written by Kafka Connect (source) – films and genres from the database. */
    public static final String DB_INFO_FILMS  = "CinemaDBInfoFilms";
    public static final String DB_INFO_GENRES = "CinemaDBInfoGenres";

    /** Written by RentalsProducer – customer rentals and purchases. */
    public static final String RENTALS         = "CinemaRentalsTopic";

    /** Written by LicensingProducer – licensing fees paid to studios. */
    public static final String LICENSING       = "CinemaLicensingTopic";

    // ── Output / Results topics (written by Kafka Streams → sink connector) ──
    public static final String OUT_REVENUE_PER_FILM       = "CinemaRevenuePerFilm";
    public static final String OUT_EXPENSES_PER_FILM      = "CinemaExpensesPerFilm";
    public static final String OUT_PROFIT_PER_FILM        = "CinemaProfitPerFilm";
    public static final String OUT_TOTAL_REVENUE          = "CinemaTotalRevenue";
    public static final String OUT_TOTAL_EXPENSES         = "CinemaTotalExpenses";
    public static final String OUT_TOTAL_PROFIT           = "CinemaTotalProfit";
    public static final String OUT_AVG_TRANSACTION_FILM   = "CinemaAvgTransactionPerFilm";
    public static final String OUT_AVG_TRANSACTION_ALL    = "CinemaAvgTransactionAllFilms";
    public static final String OUT_HIGHEST_PROFIT_FILM    = "CinemaHighestProfitFilm";
    public static final String OUT_REVENUE_LAST_HOUR      = "CinemaRevenueLastHour";
    public static final String OUT_EXPENSES_LAST_HOUR     = "CinemaExpensesLastHour";
    public static final String OUT_PROFIT_LAST_HOUR       = "CinemaProfitLastHour";
    public static final String OUT_TOP_GENRE_PER_FILM     = "CinemaTopGenrePerFilm";
}
