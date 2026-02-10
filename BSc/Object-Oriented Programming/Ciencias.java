/**
 * Classe Ciencias que estende a classe abstrata Pergunta.
 * Especializa a classe Pergunta para perguntas relacionadas à categoria de Ciências.
 */
public class Ciencias extends Pergunta {

        private String respostaDificil;

        /**
         * Construtor para a classe Ciencias.
         *
         * @param categoria       Categoria da pergunta. Espera-se que seja "Ciências" ou uma subcategoria relacionada.
         * @param texto           Texto da pergunta.
         * @param respostas       Opções de respostas para a pergunta.
         * @param respostaDificil Resposta considerada mais difícil para a pergunta.
         * @param respostaCorreta Resposta correta da pergunta.
         */
        public Ciencias(String categoria, String texto, String respostas, String respostaDificil, String respostaCorreta) {
                super(categoria, texto, respostas, respostaCorreta);
                this.respostaDificil = respostaDificil;
        }

        /**
         * Retorna a resposta considerada mais difícil para a pergunta.
         *
         * @return A resposta difícil.
         */
        @Override
        public String getRespostaDificil() {
                return respostaDificil;
        }

        /**
         * Calcula a pontuação para uma pergunta de Ciências.
         * Nesta implementação, adiciona 5 pontos à pontuação base definida na superclasse Pergunta.
         *
         * @return Pontuação calculada para a pergunta.
         */
        @Override
        public int calcularPontuacao() {
                int pontuacao = getPontuacao();
                return pontuacao += 5;
        }

        /**
         * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Ciências.
         *
         * @return Sempre retorna null, pois não é aplicável para perguntas de Ciências.
         */
        @Override
        public String getJogadores() {
                return null;
        }

        /**
         * Método sobrescrito da classe Pergunta. Não aplicável para a categoria Ciências.
         *
         * @return Sempre retorna null, pois não é aplicável para perguntas de Ciências.
         */
        @Override
        public String getJogadorResposta() {
                return null;
        }
}
