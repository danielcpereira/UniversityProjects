package com.googol.web.services;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

/**
 * Serviço que chama o servidor Ollama local via REST para gerar
 * uma análise contextualizada baseada nos termos da pesquisa.
 */
@Service
@Primary
public class OllamaChatService implements ChatService {

    @Value("${ollama.api.url}")
    private String ollamaApiUrl;

    @Value("${ollama.model}")
    private String modelName;

    private final RestTemplate rest = new RestTemplate();

    /**
     * Gera uma análise textual baseada só na query.
     */
    @Override
    public String generateAnalysis(String query, List<String> citations) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("És um assistente que fornece uma análise contextualizada de uma pesquisa.\n");
        prompt.append("Responde em português.\n\n");
        prompt.append("Termos da pesquisa: \"").append(query).append("\"\n\n");
        prompt.append("Fornece uma análise sobre esses termos.");


        Map<String, Object> body = new HashMap<>();
        body.put("model", modelName);
        body.put("prompt", prompt.toString());
        body.put("stream", false);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String,Object>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<Map> response = rest.exchange(ollamaApiUrl, HttpMethod.POST, request, Map.class);
            Map<?,?> respBody = response.getBody();
            if (respBody != null && respBody.containsKey("response")) {
                return respBody.get("response").toString().trim();
            }
            return "Não foi possível obter resposta do Ollama.";
        } catch (RestClientException ex) {
            return "Erro na análise do Ollama: " + ex.getMessage();
        }
    }
}
