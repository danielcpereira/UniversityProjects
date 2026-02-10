package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

/**
 * Controlador para obter links que apontam para um URL específico.
 */
@Controller
public class LinksController {

    private final GatewayService gatewayService;

    /**
     * Construtor
     */
    public LinksController(GatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    /**
     * GET
     * Mostra a lista de links que apontam para a URL fornecida.
     */
    @GetMapping("/links")
    public String showLinks(@RequestParam(value = "url", required = false) String url, Model model) {
        if (url != null) {
            List<String> links = gatewayService.linksToUrl(url);
            model.addAttribute("links", links);
            model.addAttribute("url", url);
        }
        return "links";
    }
}