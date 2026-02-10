/**
 * Classe Futebol que estende a classe Desporto.
 * Especializa a classe Desporto para perguntas específicas da categoria de Futebol.
 */
public class Futebol extends Desporto {

    private String jogadores;       // Lista de jogadores relacionados à pergunta.
    private String jogadorResposta; // Resposta correta no contexto de jogadores de futebol.

    /**
     * Construtor para a classe Futebol.
     *
     * @param categoria       Categoria da pergunta, esperada ser "Futebol" ou uma subcategoria relacionada.
     * @param texto           Texto da pergunta.
     * @param respostas       Opções de respostas para a pergunta.
     * @param respostaCorreta Resposta correta da pergunta.
     * @param jogadores       Lista de jogadores relacionados à pergunta.
     * @param jogadorResposta Resposta correta no contexto de jogadores de futebol.
     */
    public Futebol(String categoria, String texto, String respostas, String respostaCorreta, String jogadores, String jogadorResposta) {
        super(categoria, texto, respostas, respostaCorreta);
        this.jogadores = jogadores;
        this.jogadorResposta = jogadorResposta;
    }

    /**
     * Retorna a lista de jogadores relacionados à pergunta de futebol.
     *
     * @return Lista de jogadores.
     */
    @Override
    public String getJogadores() {
        return jogadores;
    }

    /**
     * Retorna a resposta correta no contexto de jogadores de futebol.
     *
     * @return Resposta do jogador.
     */
    @Override
    public String getJogadorResposta() {
        return jogadorResposta;
    }

    /**
     * Calcula a pontuação para uma pergunta de Futebol.
     * Nesta implementação, adiciona 4 pontos à pontuação base definida na superclasse Pergunta.
     *
     * @return Pontuação calculada para a pergunta.
     */
    @Override
    public int calcularPontuacao() {
        int pontuacao = getPontuacao();
        return pontuacao += 4;
    }
}
