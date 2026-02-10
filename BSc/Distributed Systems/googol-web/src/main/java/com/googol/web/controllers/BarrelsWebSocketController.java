package com.googol.web.controllers;

import com.googol.web.services.GatewayService;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Controller;

import java.util.List;

/**
 * Permite que clientes recebam as informações dos Barrels em tempo real
 */
@Controller
public class BarrelsWebSocketController {
    private final SimpMessagingTemplate messagingTemplate;
    private final GatewayService gatewayService;

    /**
     * Construtor
     * SimpMessagingTemplate: para enviar mensagens
     * GatewayService: para obter informações do estado dos barrels
     */
    public BarrelsWebSocketController(SimpMessagingTemplate messagingTemplate, GatewayService gatewayService) {
        this.messagingTemplate = messagingTemplate;
        this.gatewayService = gatewayService;
    }

    @MessageMapping("/barrels")
    @SendTo("/topic/barrels")
    public List<GatewayService.BarrelInfo> requestBarrels() {
        return gatewayService.getBarrelsInfo();
    }

    /**
     * A cada 5 segundos, este método é executado pelo Scheduler do Spring.
     * O Scheduler possibilita a execução de tarefas de forma programada sem necessidade de threads
     *
     * Procura novamente o estado dos Barrels e envia
     * automaticamente uma mensagem para "/topic/barrels"
     */
    @Scheduled(fixedRate = 5000)
    public void pushBarrelsInfo() {
        List<GatewayService.BarrelInfo> barrels = gatewayService.getBarrelsInfo();
        messagingTemplate.convertAndSend("/topic/barrels", barrels);
    }
}
