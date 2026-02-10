/**
 * Classe Natacao que estende a classe Desporto.
 * Especializa a classe Desporto para perguntas específicas da categoria de Natação.
 */
public class Natacao extends Desporto {

        /**
         * Construtor para a classe Natacao.
         *
         * @param categoria       Categoria da pergunta, esperada ser "Natação" ou uma subcategoria relacionada.
         * @param texto           Texto da pergunta.
         * @param respostas       Opções de respostas para a pergunta.
         * @param respostaCorreta Resposta correta da pergunta.
         */
        public Natacao(String categoria, String texto, String respostas, String respostaCorreta) {
                super(categoria, texto, respostas, respostaCorreta);
        }

        /**
         * Calcula a pontuação para uma pergunta de Natação.
         * Nesta implementação, adiciona 13 pontos à pontuação base definida na superclasse Pergunta.
         *
         * @return Pontuação calculada para a pergunta.
         */
        @Override
        public int calcularPontuacao() {
                int pontuacao = getPontuacao();
                return pontuacao += 13;
        }}
