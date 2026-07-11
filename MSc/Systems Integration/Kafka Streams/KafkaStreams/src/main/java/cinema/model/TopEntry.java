package cinema.model;

/** Tracks the top film by profit or top genre by revenue for a given key. */
public class TopEntry {
    private String label;   // film title or genre name
    private double value;

    public TopEntry() {}

    public TopEntry(String label, double value) {
        this.label = label;
        this.value = value;
    }

    public String getLabel() { return label; }
    public double getValue() { return value; }

    /** Update only if the new value is strictly greater. */
    public TopEntry update(String newLabel, double newValue) {
        if (newValue > this.value) {
            this.label = newLabel;
            this.value = newValue;
        }
        return this;
    }
}
