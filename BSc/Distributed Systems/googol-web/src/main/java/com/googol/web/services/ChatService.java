package com.googol.web.services;

import java.util.List;

/**
 * Interface para serviços de análise contextualizada.
 */
public interface ChatService {
    /**
     * Gera uma análise baseada na query.
     *
     * @param query termo de pesquisa
     * @param citations
     * @return texto da análise
     */
    String generateAnalysis(String query, List<String> citations);
}
