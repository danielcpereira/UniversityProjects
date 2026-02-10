/**
 * Classe Desporto que estende a classe abstrata Pergunta.
 * Especializa a classe Pergunta para perguntas relacionadas à categoria de Desporto.
 */
public class Desporto extends Pergunta {

        /**
         * Construtor para a classe Desporto.
         *
         * @param categoria       Categoria da pergunta. Espera-se que seja "Desporto" ou uma subcategoria relacionada.
         * @param texto           Texto da pergunta.
         * @param respostas       Opções de respostas para a pergunta.
         * @param respostaCorreta Resposta correta da pergunta.
         */
        public Desporto(String categoria, String texto, String respostas, String respostaCorreta) {
                super(categoria, texto, respostas, respostaCorreta);
        }

        /**
         * Calcula a pontuação para uma pergunta de Desporto.
         * Nesta implementação, a pontuação é sempre 0. Esta implementação pode precisar de revisão.
         *
         * @return Pontuação calculada para a pergunta, que é 0 neste caso.
         */
        @Override
        public int calcularPontuacao() {
                return 0;
        }

        /**
         * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Desporto.
         *
         * @return Sempre retorna null, pois não é aplicável para perguntas de Desporto.
         */
        @Override
        public String getJogadores() {
                return null;
        }

        /**
         * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Desporto.
         *
         * @return Sempre retorna null, pois não é aplicável para perguntas de Desporto.
         */
        @Override
        public String getJogadorResposta() {
                return null;
        }

        /**
         * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Desporto.
         *
         * @return Sempre retorna null, pois não é aplicável para perguntas de Desporto.
         */
        @Override
        public String getRespostaDificil() {
                return null;
        }

}
