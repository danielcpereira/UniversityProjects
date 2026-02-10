import java.io.*;

/**
 * Classe abstrata Pergunta que implementa Serializable.
 * Representa uma pergunta genérica em um jogo de perguntas e respostas.
 */
abstract class Pergunta implements Serializable{

    private String texto;
    private String categoria;
    private String respostas;
    private String respostaCorreta;
    private int pontuacao = 5;

    /**
     * Construtor para a classe Pergunta.
     *
     * @param categoria        Categoria da pergunta.
     * @param texto            Texto da pergunta.
     * @param respostas        Opções de respostas para a pergunta.
     * @param respostaCorreta  Resposta correta da pergunta.
     */
    public Pergunta(String categoria, String texto, String respostas, String respostaCorreta) {
        this.categoria = categoria;
        this.texto = texto;
        this.respostas = respostas;
        this.respostaCorreta = respostaCorreta;
    }

    /**
     * Retorna o texto da pergunta.
     *
     * @return Texto da pergunta.
     */
    public String getTexto() {
        return texto;
    }

    /**
     * Retorna a categoria da pergunta.
     *
     * @return Categoria da pergunta.
     */
    public String getCategoria() {
        return categoria;
    }

    /**
     * Retorna as opções de respostas da pergunta.
     *
     * @return Respostas da pergunta.
     */
    public String getRespostas() {
        return respostas;
    }


    public String getRespostaCorreta() {
        return respostaCorreta;
    }
    /**
     * Retorna a pontuação atribuída à pergunta.
     *
     * @return Pontuação da pergunta.
     */
    public int getPontuacao() {
        return pontuacao;
    }
    /**
     * Método abstrato para calcular a pontuação da pergunta.
     *
     * @return Pontuação calculada.
     */
    public abstract int calcularPontuacao();
    /**
     * Método abstrato para obter os jogadores relacionados à pergunta.
     *
     * @return Jogadores relacionados.
     */
    public abstract String getJogadores() ;
    /**
     * Método abstrato para obter a resposta do jogador para a pergunta.
     *
     * @return Resposta do jogador.
     */
    public abstract String getJogadorResposta();
    /**
     * Método abstrato para obter a resposta difícil para a pergunta.
     *
     * @return Resposta difícil.
     */
    public abstract String getRespostaDificil() ;
    /**
     * Retorna uma representação em String da pergunta.
     *
     * @return Representação em String da pergunta.
     */
    @Override
    public String toString() {
        return "Pergunta{" +
                "texto='" + texto + '\'' +
                ", tipo='" + categoria + '\'' +
                ", respostas='" + respostas + '\'' +
                ", respostaCorreta='" + respostaCorreta + '\'' +
                ", pontuacao=" + pontuacao +
                '}';
    }

}
