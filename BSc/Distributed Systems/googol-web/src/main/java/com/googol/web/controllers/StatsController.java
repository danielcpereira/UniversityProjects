package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Controlador para fornecer estatísticas de pesquisa.
 */
@RestController
@RequestMapping("/api/stats")
public class StatsController {

    private final GatewayService gatewayService;

    /**
     * Construtor
     */
    public StatsController(GatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    /**
     * Retorna o Top 10 de pesquisas.
     * @return StatsResponse palavra->contagem
     */
    @GetMapping
    public StatsResponse getStats() {
        Map<String, Integer> topSearches = gatewayService.readStatisticsFromFile("estatisticas.txt");
        return new StatsResponse(topSearches);
    }

    /**
     * Resposta das estatísticas.
     */
    public static class StatsResponse {
        private final Map<String, Integer> topSearches;

        public StatsResponse(Map<String, Integer> topSearches) {
            this.topSearches = topSearches;
        }

        public Map<String, Integer> getTopSearches() {
            return topSearches;
        }
    }
}