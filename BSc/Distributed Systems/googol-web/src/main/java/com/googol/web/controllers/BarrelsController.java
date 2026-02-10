package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;


/**
 * Controlador responsável por lidar com as requisições da página de barrels ativos.
 */
@Controller
public class BarrelsController {
    private final GatewayService gatewayService;

    /**
     * Construtor do controlador.
     *
     * @param serviço que fornece dados dos barrels
     */
    public BarrelsController(GatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    /**
     * Mapeia requisições GET para "/barrels".
     * Obtém a lista de barrels ativos e adiciona ao modelo para renderização na view.
     *
     * @param model para Thymeleaf
     * @return "barrels.html"
     */
    @GetMapping("/barrels")
    public String showBarrels(Model model) {
        model.addAttribute("barrels", gatewayService.getBarrelsInfo());
        return "barrels";
    }
}
