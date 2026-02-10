package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.Map;

/**
 * Controlador para exibir a página de estatísticas.
 */
@Controller
public class StatsViewController {

    private final GatewayService gatewayService;

    /**
     * Construtor
     */
    public StatsViewController(GatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    /**
     * GET
     * Exibe as estatisticas na pagina stats.html.
     */
    @GetMapping("/stats")
    public String statsView(Model model) {
        Map<String, Integer> topSearches = gatewayService.readStatisticsFromFile("estatisticas.txt");
        model.addAttribute("topSearches", topSearches);
        return "stats";
    }
}
