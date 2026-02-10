/**
 * Classe Artes que estende a classe abstrata Pergunta.
 * Especializa a classe Pergunta para perguntas relacionadas à categoria de Artes.
 */
public class Artes extends Pergunta {

    /**
     * Construtor para a classe Artes.
     *
     * @param categoria       Categoria da pergunta. Espera-se que seja "Artes" ou uma subcategoria relacionada.
     * @param texto           Texto da pergunta.
     * @param respostas       Opções de respostas para a pergunta.
     * @param respostaCorreta Resposta correta da pergunta.
     */
    public Artes(String categoria, String texto, String respostas, String respostaCorreta) {
        super(categoria, texto, respostas, respostaCorreta);
    }

    /**
     * Calcula a pontuação para uma pergunta de Artes.
     * Nesta implementação, a pontuação é dez vezes a pontuação base definida na superclasse Pergunta.
     *
     * @return Pontuação calculada para a pergunta.
     */
    @Override
    public int calcularPontuacao() {
        int pontuacao = getPontuacao();
        return pontuacao *= 10;
    }

    /**
     * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Artes.
     *
     * @return Sempre retorna null, pois não é aplicável para perguntas de Artes.
     */
    @Override
    public String getJogadores() {
        return null;
    }

    /**
     * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Artes.
     *
     * @return Sempre retorna null, pois não é aplicável para perguntas de Artes.
     */
    @Override
    public String getJogadorResposta() {
        return null;
    }

    /**
     * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Artes.
     *
     * @return Sempre retorna null, pois não é aplicável para perguntas de Artes.
     */
    @Override
    public String getRespostaDificil() {
        return null;
    }

}
