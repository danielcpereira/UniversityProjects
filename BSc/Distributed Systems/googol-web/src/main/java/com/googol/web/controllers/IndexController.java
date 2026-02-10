package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.net.MalformedURLException;
import java.net.URL;

/**
 * Controlador para a página inicial
 * e indexação de URLs.
 */
@Controller
public class IndexController {

    private final GatewayService gatewayService;

    /**
     * Construtor
     */
    public IndexController(GatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    /**
     * GET
     * Mostra a página inicial com a barra de pesquisa.
     */
    @GetMapping("/")
    public String showIndex(Model model) {
        return "home";
    }

    /**
     * GET
     * Mostra a indexação de URLs.
     */
    @GetMapping("/index-form")
    public String indexForm() {
        return "index_form";
    }

    /**
     * POST
     * Processa um URL a indexar.
     */
    @PostMapping("/home")
    public String indexUrl(@RequestParam("url") String url, RedirectAttributes redirectAttributes) {
        try {
            new URL(url);
        } catch (MalformedURLException e) {
            redirectAttributes.addFlashAttribute("errorMessage", "URL inválido. Por favor, insira um URL válido.");

            return "redirect:/index-form";
        }

        gatewayService.sendUrlToQueue(url);
        redirectAttributes.addFlashAttribute("successMessage",
                "URL enviado com sucesso!");

        return "redirect:/";
    }
}
