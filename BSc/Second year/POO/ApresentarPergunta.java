import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Random;

/**
 * Classe ApresentarPergunta que estende JFrame.
 * Responsável por apresentar perguntas ao usuário e gerenciar a interação.
 */
public class ApresentarPergunta extends JFrame {
    private JFrame ApresentarPergunta;
    private Pergunta perguntaAleatoria;
    private JPanel painelBotoes;
    private String respostaSelecionada;
    private int pontuacao;
    private int perguntaNumero=0;
    private String respostaCorreta;
    private ArrayList<Pergunta> perguntasCertas = new ArrayList<>();
    private ArrayList<Pergunta> perguntasErradas = new ArrayList<>();
    private ArrayList<Pergunta> perguntas;

    /**
     * Construtor para a classe ApresentarPergunta.
     *
     * @param perguntas Lista de perguntas a serem apresentadas.
     */
    public ApresentarPergunta(ArrayList<Pergunta> perguntas) {
        ApresentarPergunta = this;
        this.perguntas = perguntas;
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(300, 300);
        setLayout(new BorderLayout());
        setVisible(true);
        setLocationRelativeTo(null);
        respostaSelecionada = "";
        pergunta();
    }

    /**
     * Método privado para apresentar uma pergunta.
     * Configura a interface gráfica para mostrar a pergunta e as opções de resposta.
     */
    private void pergunta(){

        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(300, 300);
        setLayout(new BorderLayout());
        setVisible(true);

        respostaSelecionada="";

        perguntaAleatoria = escolherPerguntaRandom(perguntas, perguntasErradas, perguntasCertas);
        //System.out.println(perguntaAleatoria.getTexto());
        JLabel texto = new JLabel(perguntaAleatoria.getTexto());
        texto.setVerticalAlignment(JLabel.NORTH);  // Adicionando setVerticalAlignment
        add(texto, BorderLayout.CENTER);

        texto.setVisible(true);

        painelBotoes = new JPanel(new GridLayout(0, 1)); // GridLayout com uma coluna
        add(painelBotoes, BorderLayout.SOUTH);

        if (perguntaAleatoria.getCategoria().equals("Desporto/Ski") || perguntaAleatoria.getCategoria().equals("Desporto/Natação")) {
            cortaRespostasImprime(perguntaAleatoria.getRespostas(), perguntaAleatoria.getRespostaCorreta(), 5);
            pontuacao=perguntaAleatoria.calcularPontuacao();
            respostaCorreta=perguntaAleatoria.getRespostaCorreta();
        }
        if (perguntaAleatoria.getCategoria().equals("Desporto/Futebol")) {
            if (perguntaNumero < 2) {
                cortaRespostasImprime(perguntaAleatoria.getJogadores(), perguntaAleatoria.getJogadorResposta(), 5);
                respostaCorreta=perguntaAleatoria.getJogadorResposta();
                pontuacao=perguntaAleatoria.calcularPontuacao();
            }
            if (perguntaNumero>= 2) {
                cortaRespostasImprime(perguntaAleatoria.getRespostas(), perguntaAleatoria.getRespostaCorreta(), 5);
                pontuacao = perguntaAleatoria.getPontuacao();
                pontuacao=perguntaAleatoria.calcularPontuacao();
                respostaCorreta = perguntaAleatoria.getRespostaCorreta();
            }
        }
        if (perguntaAleatoria.getCategoria().equals("Ciências")) {
            pontuacao=perguntaAleatoria.calcularPontuacao();
            if (perguntaNumero < 2) {
                cortaRespostasImprime(perguntaAleatoria.getRespostas(), perguntaAleatoria.getRespostaCorreta(), 5);
                respostaCorreta= perguntaAleatoria.getRespostaCorreta();
            }
            if (perguntaNumero >= 2) {
                cortaRespostasImprime(perguntaAleatoria.getRespostaDificil(), perguntaAleatoria.getRespostaCorreta(), 5);
                respostaCorreta= perguntaAleatoria.getRespostaCorreta();
            }
        }
        if (perguntaAleatoria.getCategoria().equals("Artes")) {
            pontuacao=perguntaAleatoria.calcularPontuacao();
            if (perguntaNumero < 2) {
                cortaRespostasImprime(perguntaAleatoria.getRespostas(), perguntaAleatoria.getRespostaCorreta(), 3);
                respostaCorreta=perguntaAleatoria.getRespostaCorreta();
            }
            if (perguntaNumero >= 2) {
                cortaRespostasImprime(perguntaAleatoria.getRespostas(), perguntaAleatoria.getRespostaCorreta(), 5);
                respostaCorreta=perguntaAleatoria.getRespostaCorreta();
            }
        }
        painelBotoes.setVisible(true);
        validate();
        repaint();
        perguntaNumero++;
        //System.out.println(perguntaNumero);
    }

    /**
     * Classe interna ButtonClickListener que implementa ActionListener.
     * Responsável por lidar com ações do botão na interface gráfica.
     */
    private class ButtonClickListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            JButton sourceButton = (JButton) e.getSource();
            respostaSelecionada = sourceButton.getText();
            //System.out.println(respostaSelecionada);
            if(respostaSelecionada.equals(respostaCorreta)){
                JOptionPane.showMessageDialog(null, "Correto!\nPontuação="+pontuacao);
                perguntasCertas.add(perguntaAleatoria);
                caminho();
            }
            else{
                JOptionPane.showMessageDialog(null, "Errado!");
                perguntasErradas.add(perguntaAleatoria);
                caminho();
            }
        }
    }

    /**
     * Apresenta uma interface gráfica para mostrar o top 3 de pontuações.
     *
     * @param jogador Objeto Jogador contendo informações sobre o jogador atual.
     */
    public void top3GUI(Jogador jogador) {
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(300, 300);
        setLayout(new BorderLayout());
        setLocationRelativeTo(null);
        setVisible(true);

        String top3String = jogador.top3();
        String[] top3Array = top3String.split("\n");

        StringBuilder sb = new StringBuilder("Top 3 Melhores Pontuações:\n\n");
        for (String s : top3Array) {
            // Formata a string para o novo formato de data e hora
            String formattedString = s.trim().replaceAll("(\\d{2})(\\d{2})(\\d{4})(\\d{2})(\\d{2})", "$1/$2/$3 $4:$5");
            sb.append(formattedString).append("\n");
        }

        sb.append("\nSua pontuação: ").append(jogador.calcularPontuacaoTotal(jogador.getPerguntasCertas()));

        // Usando JTextArea em vez de JLabel
        JTextArea textArea = new JTextArea(sb.toString());
        textArea.setEditable(false);  // torna o JTextArea não editável
        textArea.setOpaque(false);    // torna o JTextArea transparente
        textArea.setAlignmentX(JTextArea.CENTER_ALIGNMENT); // centraliza o texto

        // Adicionando JTextArea ao painel
        add(textArea, BorderLayout.CENTER);

        JButton button = new JButton("Menu");
        add(button, BorderLayout.SOUTH);
        button.setVisible(true);
        button.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                dispose();
                new POOTriviaApp();

            }
        });
    }

    /**
     * Método privado para determinar o próximo passo após uma resposta ser selecionada.
     * Decidirá se uma nova pergunta deve ser apresentada ou se o jogo terminou.
     */
    private void caminho(){
        if(perguntaNumero<5){
            getContentPane().removeAll();
            revalidate();
            repaint();
            pergunta();
        }
        else{
            ApresentarPergunta.dispose();
            getContentPane().removeAll();
            revalidate();
            repaint();
            dispose();
            LocalDateTime horaInicio = LocalDateTime.now();
            String nomeJogador = obterNomeUsuario();
            Jogador jogador = new Jogador(nomeJogador,  horaInicio, perguntasCertas, perguntasErradas);
            jogador.salvarDadosJogador(jogador);
            //System.out.println("Nome do usuário: " + nomeJogador);
            top3GUI(jogador);
        }
    }

    /**
     * Solicita ao usuário que insira seu nome.
     *
     * @return Nome do usuário.
     */
    private String obterNomeUsuario() {
        String nome = JOptionPane.showInputDialog("Digite seu nome:");
        if (nome == null || nome.trim().isEmpty()) {
            JOptionPane.showMessageDialog(null, "Você precisa fornecer um nome para continuar.", "Erro", JOptionPane.ERROR_MESSAGE);
            return obterNomeUsuario();
        } else {
            return nome.trim();
        }
    }


    /**
     * Método privado para processar as respostas e apresentá-las na interface gráfica.
     *
     * @param respostas        String com as respostas a serem cortadas.
     * @param respostaCorreta  Resposta correta para a pergunta.
     * @param maxRespostas     Número máximo de respostas a serem exibidas.
     */
    private void cortaRespostasImprime(String respostas, String respostaCorreta, int maxRespostas) {
        ArrayList<String> respostasCortadas = new ArrayList<>();
        String[] todasRespostas = respostas.split(",");
        for (String resposta : todasRespostas) {
            respostasCortadas.add(resposta.trim());
        }
        if (!respostasCortadas.contains(respostaCorreta)) {
            respostasCortadas.add(respostaCorreta);
        }
        Random rand = new Random();
        while (respostasCortadas.size() > maxRespostas) {
            int removeIndex = rand.nextInt(respostasCortadas.size());
            if (!respostasCortadas.get(removeIndex).equals(respostaCorreta)) {
                respostasCortadas.remove(removeIndex);
            }
        }
        Collections.shuffle(respostasCortadas, rand);
        painelBotoes.removeAll();

        for (String respostasCortada : respostasCortadas) {
            //System.out.println(respostasCortadas.get(i));
            JButton button = new JButton(respostasCortada);
            button.addActionListener(new ButtonClickListener());
            button.setPreferredSize(new Dimension(200, 50));
            painelBotoes.add(button);
            //System.out.println((i + 1) + ") " + respostasCortadas.get(i));
        }
        painelBotoes.setVisible(true);
    }

    /**
     * Escolhe aleatoriamente uma pergunta a ser apresentada, evitando perguntas já respondidas.
     *
     * @param perguntas        Lista de todas as perguntas.
     * @param perguntasErradas Lista de perguntas respondidas incorretamente.
     * @param perguntasCertas  Lista de perguntas respondidas corretamente.
     * @return Pergunta aleatória selecionada.
     */
    private Pergunta escolherPerguntaRandom(ArrayList<Pergunta> perguntas, ArrayList<Pergunta> perguntasErradas, ArrayList<Pergunta> perguntasCertas) {
        int indiceAleatorio;
        do {
            indiceAleatorio = (int) (Math.random() * perguntas.size());
        } while (perguntasErradas.contains(perguntas.get(indiceAleatorio)) || perguntasCertas.contains(perguntas.get(indiceAleatorio)));
        return perguntas.get(indiceAleatorio);
    }
}
