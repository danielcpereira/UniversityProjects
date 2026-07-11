package cinema.cli;

import com.google.gson.*;

import java.io.*;
import java.net.URI;
import java.net.http.*;
import java.util.*;

/**
 * Administrator CLI for the Cinema Streaming Platform.
 * Communicates with the REST server over HTTP.
 *
 * Usage: java -cp target/cinema-streaming-1.0.0.jar cinema.cli.AdminCLI
 */
public class AdminCLI {

    private static final String BASE_URL = "http://localhost:7000";
    private static final HttpClient HTTP  = HttpClient.newHttpClient();
    private static final Gson       GSON  = new GsonBuilder().setPrettyPrinting().create();

    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(System.in);
        System.out.println("╔══════════════════════════════════════╗");
        System.out.println("║  Cinema Streaming – Admin CLI        ║");
        System.out.println("╚══════════════════════════════════════╝");

        while (true) {
            printMenu();
            System.out.print("Choice: ");
            String choice = sc.nextLine().trim();
            try {
                handleChoice(choice, sc);
            } catch (Exception e) {
                System.out.println("✗ Error: " + e.getMessage());
            }
        }
    }

    private static void printMenu() {
        System.out.println("""

            ─── Catalogue ──────────────────────────────
             1) List genres
             2) Add genre
             3) List films
             4) Add film
             5) Update film
            ─── Statistics ─────────────────────────────
             6) Revenue per film            (req 5)
             7) Expenses per film           (req 6)
             8) Profit per film             (req 7)
             9) Total revenue               (req 8)
            10) Total expenses              (req 9)
            11) Total profit                (req 10)
            12) Avg transaction per film    (req 11)
            13) Avg transaction all films   (req 12)
            14) Film with highest profit    (req 13)
            15) Revenue last hour           (req 14)
            16) Expenses last hour          (req 15)
            17) Profit last hour            (req 16)
            18) Top genre per film          (req 17)
             0) Exit
            ────────────────────────────────────────────""");
    }

    private static void handleChoice(String choice, Scanner sc) throws Exception {
        switch (choice) {
            case "1"  -> get("/genres");
            case "2"  -> {
                System.out.print("Genre name: ");
                String name = sc.nextLine().trim();
                post("/genres", Map.of("genre_name", name));
            }
            case "3"  -> get("/films");
            case "4"  -> {
                System.out.print("Film title: ");
                String title = sc.nextLine().trim();
                System.out.print("Genre ID (see list genres): ");
                int genreId = Integer.parseInt(sc.nextLine().trim());
                System.out.print("Base price (€): ");
                double price = Double.parseDouble(sc.nextLine().trim());
                post("/films", Map.of("title", title, "genre_id", genreId, "base_price", price));
            }
            case "5"  -> {
                System.out.print("Film ID to update: ");
                int id = Integer.parseInt(sc.nextLine().trim());
                System.out.print("New title: ");
                String title = sc.nextLine().trim();
                System.out.print("New genre ID: ");
                int genreId = Integer.parseInt(sc.nextLine().trim());
                System.out.print("New base price (€): ");
                double price = Double.parseDouble(sc.nextLine().trim());
                put("/films/" + id, Map.of("title", title, "genre_id", genreId, "base_price", price));
            }
            case "6"  -> get("/stats/revenue-per-film");
            case "7"  -> get("/stats/expenses-per-film");
            case "8"  -> get("/stats/profit-per-film");
            case "9"  -> get("/stats/total-revenue");
            case "10" -> get("/stats/total-expenses");
            case "11" -> get("/stats/total-profit");
            case "12" -> get("/stats/avg-transaction/film");
            case "13" -> get("/stats/avg-transaction/all");
            case "14" -> get("/stats/highest-profit-film");
            case "15" -> get("/stats/revenue-last-hour");
            case "16" -> get("/stats/expenses-last-hour");
            case "17" -> get("/stats/profit-last-hour");
            case "18" -> get("/stats/top-genre-per-film");
            case "0"  -> { System.out.println("Goodbye!"); System.exit(0); }
            default   -> System.out.println("Unknown option.");
        }
    }

    private static void get(String path) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + path))
                .GET().build();
        HttpResponse<String> res = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
        prettyPrint(res.body());
    }

    private static void post(String path, Map<String, Object> body) throws Exception {
        String json = GSON.toJson(body);
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + path))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json)).build();
        HttpResponse<String> res = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
        System.out.println("✓ " + res.body());
    }

    private static void put(String path, Map<String, Object> body) throws Exception {
        String json = GSON.toJson(body);
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + path))
                .header("Content-Type", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(json)).build();
        HttpResponse<String> res = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
        System.out.println("✓ " + res.body());
    }

    private static void prettyPrint(String json) {
        try {
            JsonElement el = JsonParser.parseString(json);
            System.out.println(GSON.toJson(el));
        } catch (Exception e) {
            System.out.println(json);
        }
    }
}
