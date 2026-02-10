package com.googol.web.services;

import com.googol.meta1.GatewayHeader;
import com.googol.meta1.BarrelStats;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Serviço que faz a ponte entre a web e o servidor rmi
 */
@Service
public class GatewayService {

    @Value("${rmi.server.host}")
    private String rmiHost;

    @Value("${rmi.registry.port}")
    private int rmiPort;

    private GatewayHeader gateway;

    @PostConstruct
    public void init() {
        try {
            String url = String.format("rmi://%s:%d/Gateway", rmiHost, rmiPort);
            this.gateway = (GatewayHeader) Naming.lookup(url);
        } catch (Exception e) {
            throw new RuntimeException("Não foi possível conectar ao RMI Gateway em " + rmiHost + ":" + rmiPort, e);
        }
    }

    public void sendUrlToQueue(String link) {
        try {
            gateway.sendUrlToQueue(link);
        } catch (IOException | NotBoundException e) {
            throw new RuntimeException("Erro ao enviar URL para a fila", e);
        }
    }

    public List<String> searchWords(String query) {
        try {
            return gateway.searchWords(query);
        } catch (RemoteException e) {
            throw new RuntimeException("Erro na busca de palavras", e);
        }
    }

    public List<String> linksToUrl(String url) {
        try {
            return gateway.linksToUrl(url);
        } catch (IOException | NotBoundException e) {
            throw new RuntimeException("Erro ao obter links que apontam para a URL", e);
        }
    }

    public Map<String, Integer> readStatisticsFromFile(String statsFile) {
        try {
            return gateway.readStatisticsFromFile(statsFile);
        } catch (RemoteException e) {
            throw new RuntimeException("Erro ao ler estatísticas do ficheiro", e);
        }
    }

    public void updateStatistics(String word) {
        try {
            gateway.updateStatistics(word);
        } catch (RemoteException e) {
            throw new RuntimeException("Erro ao atualizar estatísticas", e);
        }
    }

    public void addToIndex(String url, String title, String description, List<String> words, List<String> pageLinks) {
        try {
            gateway.addToIndex(url, title, description, words, pageLinks);
        } catch (RemoteException e) {
            throw new RuntimeException("Erro ao adicionar dados ao índice", e);
        }
    }

    public List<String> searchInIndex(String word) {
        try {
            return gateway.searchInIndex(word);
        } catch (IOException e) {
            throw new RuntimeException("Erro na pesquisa do índice", e);
        }
    }

    public List<String> findLinksToUrl(String url) {
        try {
            return gateway.findLinksToUrl(url);
        } catch (IOException e) {
            throw new RuntimeException("Erro na pesquisa de inlinks", e);
        }
    }

    /**
     * Enviar dados de cada Barrel para a camada web.
     */
    public static class BarrelInfo {
        private final String name;
        private final int indexSize;
        private final double responseTime;
        private final boolean active;

        public BarrelInfo(String name, int indexSize, double responseTime, boolean active) {
            this.name = name;
            this.indexSize = indexSize;
            this.responseTime = responseTime;
            this.active = active;
        }

        public String getName() {
            return name;
        }

        public int getIndexSize() {
            return indexSize;
        }

        public double getResponseTime() {
            return responseTime;
        }

        public boolean isActive() {
            return active;
        }
    }

    /**
     * Obtém via RMI as estatísticas dos Barrels.
     */
    public List<BarrelInfo> getBarrelsInfo() {
        try {
            Map<String, BarrelStats> stats = gateway.getBarrelsInfo();
            return stats.entrySet().stream().map(e -> new BarrelInfo(e.getKey(), e.getValue().getIndexSize(), e.getValue().getAvgResponseTime(), !e.getValue().isBusy())).collect(Collectors.toList());
        } catch (RemoteException ex) {
            throw new RuntimeException("Error fetching barrels info", ex);
        }
    }
}
