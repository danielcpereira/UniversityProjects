/**
 * Classe Ski que estende a classe Desporto.
 * Especializa a classe Desporto para perguntas específicas da categoria de Ski.
 */
public class Ski extends Desporto {

        /**
         * Construtor para a classe Ski.
         *
         * @param categoria       Categoria da pergunta, esperada ser "Ski" ou uma subcategoria relacionada.
         * @param texto           Texto da pergunta.
         * @param respostas       Opções de respostas para a pergunta.
         * @param respostaCorreta Resposta correta da pergunta.
         */
        public Ski(String categoria, String texto, String respostas, String respostaCorreta) {
                super(categoria, texto, respostas, respostaCorreta);
        }

        /**
         * Calcula a pontuação para uma pergunta de Ski.
         * Nesta implementação, adiciona 3 pontos à pontuação base definida na superclasse Pergunta e depois dobra o valor.
         *
         * @return Pontuação calculada para a pergunta.
         */
        @Override
        public int calcularPontuacao() {
                int pontuacao = getPontuacao();
                pontuacao += 3;
                return pontuacao *= 2;
        }
}
