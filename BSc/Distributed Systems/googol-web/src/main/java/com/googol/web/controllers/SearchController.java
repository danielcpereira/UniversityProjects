package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import com.googol.web.services.ChatService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Controlador que lida com:
 * Pesquisa de termos indexados via gateway
 * Analise contextualizada via ChatService
 */
@Controller
public class SearchController {

    private final GatewayService gatewayService;
    private final ChatService chatService;
    private final int pageSize;

    /**
     * Construtor
     */
    public SearchController(GatewayService gatewayService, ChatService chatService, @Value("${app.pagination.page-size:10}") int pageSize) {
        this.gatewayService = gatewayService;
        this.chatService = chatService;
        this.pageSize = pageSize;
    }

    /**
     * GET
     * Endpoint para pesquisa de termos indexados, exibição de resultados e paginação.
     */
    @GetMapping("/search")
    public String search(@RequestParam("q") String query, @RequestParam(value = "page", defaultValue = "1") int page, Model model) {

        gatewayService.updateStatistics(query);

        List<String> allResults = gatewayService.searchWords(query);

        int total = allResults.size();
        int totalPages = (int) Math.ceil((double) total / pageSize);
        int from = (page - 1) * pageSize;
        int to = Math.min(from + pageSize, total);

        List<String> pageResults;
        if (total > 0 && from < total) {
            pageResults = allResults.subList(from, to);
        } else {
            pageResults = Collections.emptyList();
        }

        List<SearchResult> results = pageResults.stream().map(this::parseResultEntry).collect(Collectors.toList());

        model.addAttribute("query", query);
        model.addAttribute("results", results);
        model.addAttribute("currentPage", page);
        model.addAttribute("totalPages", totalPages);
        return "search";
    }

    /**
     * POST
     * Gera o texto da análise contextualizada.
     */
    @PostMapping("/search/analysis")
    @ResponseBody
    public String analysis(@RequestParam("q") String query) {
        return chatService.generateAnalysis(query, Collections.emptyList());
    }

    private SearchResult parseResultEntry(String entry) {
        String[] parts = entry.split(";", 4);

        String url;
        if (parts.length > 0) {
            url = parts[0];
        } else {
            url = "";
        }

        String title;
        if (parts.length > 1) {
            title = parts[1];
        } else {
            title = "";
        }

        String description;
        if (parts.length > 2) {
            description = parts[2];
        } else {
            description = "";
        }

        return new SearchResult(title, url, description);
    }

    /**
     * Representação de um resultado de pesquisa.
     */
    public static class SearchResult {
        private final String title;
        private final String url;
        private final String description;

        public SearchResult(String title, String url, String description) {
            if (title != null) {
                this.title = title;
            } else {
                this.title = "";
            }

            if (url != null) {
                this.url = url;
            } else {
                this.url = "";
            }

            if (description != null) {
                this.description = description;
            } else {
                this.description = "";
            }
        }

        public String getTitle() {
            return title;
        }
        public String getUrl() {
            return url;
        }
        public String getDescription() {
            return description;
        }
    }
}
