package cinema.rest;

import io.javalin.Javalin;
import io.javalin.http.Context;

import java.sql.*;
import java.util.*;

/**
 * REST API server for the Cinema Streaming Platform.
 *
 * Endpoints:
 *  GET  /genres                       → list all genres
 *  POST /genres                       → add a genre
 *  GET  /films                        → list all films
 *  POST /films                        → add a film
 *  PUT  /films/:id                    → update a film
 *
 *  GET  /stats/revenue-per-film       → req 5
 *  GET  /stats/expenses-per-film      → req 6
 *  GET  /stats/profit-per-film        → req 7
 *  GET  /stats/total-revenue          → req 8
 *  GET  /stats/total-expenses         → req 9
 *  GET  /stats/total-profit           → req 10
 *  GET  /stats/avg-transaction/film   → req 11
 *  GET  /stats/avg-transaction/all    → req 12
 *  GET  /stats/highest-profit-film    → req 13
 *  GET  /stats/revenue-last-hour      → req 14
 *  GET  /stats/expenses-last-hour     → req 15
 *  GET  /stats/profit-last-hour       → req 16
 *  GET  /stats/top-genre-per-film     → req 17
 */
public class RestServer {

    private static final String DB_URL  = "jdbc:postgresql://database:5432/project3";
    private static final String DB_USER = "postgres";
    private static final String DB_PASS = "nopass";

    public static void main(String[] args) {
        Javalin app = Javalin.create(config -> {
            config.bundledPlugins.enableCors(cors -> cors.addRule(it -> it.anyHost()));
        }).start(7000);

        // ── Genre endpoints ───────────────────────────────────────────────────
        app.get("/genres",       ctx -> ctx.json(query("SELECT genre_id, genre_name FROM genres ORDER BY genre_name")));
        app.post("/genres",      ctx -> {
            String name = ctx.bodyAsClass(Map.class).get("genre_name").toString();
            exec("INSERT INTO genres (genre_name) VALUES (?)", name);
            ctx.status(201).result("Genre created");
        });

        // ── Film endpoints ────────────────────────────────────────────────────
        app.get("/films",        ctx -> ctx.json(query(
                "SELECT f.film_id, f.title, g.genre_name, f.base_price " +
                "FROM films f JOIN genres g ON f.genre_id=g.genre_id ORDER BY f.title")));
        app.post("/films",       ctx -> {
            @SuppressWarnings("unchecked")
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            exec("INSERT INTO films (title, genre_id, base_price) VALUES (?,?,?)",
                 body.get("title").toString(),
                 Integer.parseInt(body.get("genre_id").toString()),
                 Double.parseDouble(body.get("base_price").toString()));
            ctx.status(201).result("Film created");
        });
        app.put("/films/{id}",   ctx -> {
            @SuppressWarnings("unchecked")
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            exec("UPDATE films SET title=?, genre_id=?, base_price=? WHERE film_id=?",
                 body.get("title").toString(),
                 Integer.parseInt(body.get("genre_id").toString()),
                 Double.parseDouble(body.get("base_price").toString()),
                 Integer.parseInt(ctx.pathParam("id")));
            ctx.result("Film updated");
        });

        // ── Statistics endpoints ──────────────────────────────────────────────
        app.get("/stats/revenue-per-film",     ctx -> ctx.json(query("SELECT id, revenue     FROM \"CinemaRevenuePerFilm\"     ORDER BY revenue DESC")));
        app.get("/stats/expenses-per-film",    ctx -> ctx.json(query("SELECT id, expenses    FROM \"CinemaExpensesPerFilm\"    ORDER BY expenses DESC")));
        app.get("/stats/profit-per-film",      ctx -> ctx.json(query("SELECT id, profit      FROM \"CinemaProfitPerFilm\"      ORDER BY profit DESC")));
        app.get("/stats/total-revenue",        ctx -> ctx.json(query("SELECT id, revenue     FROM \"CinemaTotalRevenue\"")));
        app.get("/stats/total-expenses",       ctx -> ctx.json(query("SELECT id, expenses    FROM \"CinemaTotalExpenses\"")));
        app.get("/stats/total-profit",         ctx -> ctx.json(query("SELECT id, profit      FROM \"CinemaTotalProfit\"")));
        app.get("/stats/avg-transaction/film", ctx -> ctx.json(query("SELECT id, avg_value, count FROM \"CinemaAvgTransactionPerFilm\"  ORDER BY avg_value DESC")));
        app.get("/stats/avg-transaction/all",  ctx -> ctx.json(query("SELECT id, avg_value, count FROM \"CinemaAvgTransactionAllFilms\"")));
        app.get("/stats/highest-profit-film",  ctx -> ctx.json(query("SELECT id, film_title, profit FROM \"CinemaHighestProfitFilm\"")));
        app.get("/stats/revenue-last-hour",    ctx -> ctx.json(query("SELECT id, revenue     FROM \"CinemaRevenueLastHour\"    ORDER BY id DESC LIMIT 1")));
        app.get("/stats/expenses-last-hour",   ctx -> ctx.json(query("SELECT id, expenses    FROM \"CinemaExpensesLastHour\"   ORDER BY id DESC LIMIT 1")));
        app.get("/stats/profit-last-hour",     ctx -> ctx.json(query("SELECT id, profit      FROM \"CinemaProfitLastHour\"     ORDER BY id DESC LIMIT 1")));
        app.get("/stats/top-genre-per-film",   ctx -> ctx.json(query("SELECT id, genre_name, revenue FROM \"CinemaTopGenrePerFilm\" ORDER BY revenue DESC")));

        System.out.println("▶ REST server listening on http://0.0.0.0:7000");
    }

    // ── DB helpers ────────────────────────────────────────────────────────────

    private static List<Map<String, Object>> query(String sql, Object... params) {
        List<Map<String, Object>> rows = new ArrayList<>();
        try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            for (int i = 0; i < params.length; i++) ps.setObject(i + 1, params[i]);
            ResultSet rs = ps.executeQuery();
            ResultSetMetaData meta = rs.getMetaData();
            int cols = meta.getColumnCount();
            while (rs.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                for (int i = 1; i <= cols; i++) row.put(meta.getColumnName(i), rs.getObject(i));
                rows.add(row);
            }
        } catch (SQLException e) {
            throw new RuntimeException("DB query failed: " + e.getMessage(), e);
        }
        return rows;
    }

    private static void exec(String sql, Object... params) {
        try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            for (int i = 0; i < params.length; i++) ps.setObject(i + 1, params[i]);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new RuntimeException("DB exec failed: " + e.getMessage(), e);
        }
    }
}