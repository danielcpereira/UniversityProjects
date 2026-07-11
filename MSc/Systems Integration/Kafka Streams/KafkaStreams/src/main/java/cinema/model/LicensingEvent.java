package cinema.model;

/**
 * Represents a licensing fee paid by the platform to a studio for a film.
 * Key   = film title  (String)
 * Value = LicensingEvent (JSON)
 */
public class LicensingEvent {

    private String filmTitle;
    private String studio;
    private double amount;     // fee paid (expense)
    private long   timestamp;

    public LicensingEvent() {}

    public LicensingEvent(String filmTitle, String studio,
                          double amount, long timestamp) {
        this.filmTitle = filmTitle;
        this.studio    = studio;
        this.amount    = amount;
        this.timestamp = timestamp;
    }

    public String getFilmTitle() { return filmTitle; }
    public String getStudio()    { return studio; }
    public double getAmount()    { return amount; }
    public long   getTimestamp() { return timestamp; }

    @Override
    public String toString() {
        return String.format("LicensingEvent{film='%s', studio='%s', amount=%.2f}",
                filmTitle, studio, amount);
    }
}
