package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Controller;

import java.util.Map;

/**
 * Controlador para manter as estatisticas sempre atualizadas.
 */
@Controller
public class StatsWebSocketController {

    private final SimpMessagingTemplate messagingTemplate;
    private final GatewayService gatewayService;

    /**
     * Construtor
     */
    public StatsWebSocketController(SimpMessagingTemplate messagingTemplate, GatewayService gatewayService) {
        this.messagingTemplate = messagingTemplate;
        this.gatewayService = gatewayService;
    }

    /**
     * Le estatisticas
     */
    @MessageMapping("/stats")
    @SendTo("/topic/stats")
    public Map<String, Integer> requestStats() {
        return gatewayService.readStatisticsFromFile("estatisticas.txt");
    }

    /**
     * Envia automaticamente estatísticas atualizadas a cada 5 segundos.
     */
    @Scheduled(fixedRate = 5000)
    public void pushStats() {
        Map<String, Integer> stats = gatewayService.readStatisticsFromFile("estatisticas.txt");
        messagingTemplate.convertAndSend("/topic/stats", stats);
    }
}