package cinema.model;

/**
 * Represents a customer rental or purchase transaction.
 * Key   = film title  (String)
 * Value = RentalEvent (JSON)
 */
public class RentalEvent {

    public enum Type     { RENT, BUY }
    public enum Quality  { HD, FULL_HD, UHD_4K }
    public enum Duration { ONE_DAY, TWO_DAYS, ONE_WEEK }

    private String   filmTitle;
    private String   genre;      // genre name – used for req. 17
    private Type     type;
    private Quality  quality;    // only relevant for RENT
    private Duration duration;   // only relevant for RENT
    private double   amount;     // total charged to customer (revenue)
    private long     timestamp;

    public RentalEvent() {}

    public RentalEvent(String filmTitle, String genre, Type type,
                       Quality quality, Duration duration,
                       double amount, long timestamp) {
        this.filmTitle = filmTitle;
        this.genre     = genre;
        this.type      = type;
        this.quality   = quality;
        this.duration  = duration;
        this.amount    = amount;
        this.timestamp = timestamp;
    }

    public String   getFilmTitle() { return filmTitle; }
    public String   getGenre()     { return genre; }
    public Type     getType()      { return type; }
    public Quality  getQuality()   { return quality; }
    public Duration getDuration()  { return duration; }
    public double   getAmount()    { return amount; }
    public long     getTimestamp() { return timestamp; }

    @Override
    public String toString() {
        return String.format("RentalEvent{film='%s', genre='%s', type=%s, quality=%s, duration=%s, amount=%.2f}",
                filmTitle, genre, type, quality, duration, amount);
    }
}
