package cinema.model;

/** Helper aggregate for computing running averages. */
public class AggregateAvg {
    private double sum;
    private long   count;

    public AggregateAvg() { this.sum = 0; this.count = 0; }

    public AggregateAvg add(double value) {
        this.sum   += value;
        this.count += 1;
        return this;
    }

    public double getSum()   { return sum; }
    public long   getCount() { return count; }
    public double getAvg()   { return count == 0 ? 0 : sum / count; }
}
