/**
 * @author André Carvalho Nº2020237655
 * @author Daniel Pereira Nº2021237092
 * @version 2.0
 */

import javax.swing.*;
import java.io.*;
import java.util.ArrayList;

/**
 * Classe POOTrivia para gerenciar um jogo de trivia.
 * Inclui funcionalidades para criar perguntas a partir de um arquivo de texto.
 */
public class POOTrivia {

    private ArrayList<Pergunta> perguntas;

    /**
     * Construtor para a classe POOTrivia.
     * Inicializa a lista de perguntas.
     */
    public POOTrivia() {
        perguntas = new ArrayList<>();
    }

    /**
     * Cria perguntas a partir de um arquivo de texto e as adiciona à lista de perguntas.
     * O arquivo de texto deve ter um formato específico, com cada linha representando uma pergunta e seus dados.
     *
     * @return Lista de perguntas criadas a partir do arquivo.
     */
    public ArrayList<Pergunta> CriaPergunta() {
        try {
            BufferedReader br = new BufferedReader(new FileReader("src/POOTrivia.txt"));
            String linha = br.readLine();
            while (linha != null) {
                String[] dados = linha.split(";");
                switch (dados[0]) {
                    case "Artes":
                        perguntas.add(new Artes(dados[0], dados[1], dados[2], dados[3]));
                        break;
                    case "Desporto/Ski":
                        perguntas.add(new Ski(dados[0], dados[1], dados[2], dados[3]));
                        break;
                    case "Desporto/Natacao":
                        perguntas.add(new Natacao(dados[0], dados[1], dados[2], dados[3]));
                        break;
                    case "Desporto/Futebol":
                        perguntas.add(new Futebol(dados[0], dados[1], dados[2], dados[3], dados[4], dados[5]));
                        break;
                    case "Ciências":
                        perguntas.add(new Ciencias(dados[0], dados[1], dados[2], dados[3], dados[4]));
                        break;
                }
                linha = br.readLine();
            }
            br.close();
        } catch (IOException e) {
            System.out.println("Erro: " + e.getMessage());
        }
        return perguntas;
    }

    /**
     * Ponto de entrada principal para o jogo.
     * Configura a interface gráfica do usuário para o jogo de trivia.
     *
     * @param args Argumentos de linha de comando (não utilizados).
     */
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new POOTriviaApp().setVisible(true));
    }
}
