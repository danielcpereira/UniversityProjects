import java.io.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.time.format.DateTimeFormatter;
/**
 * Classe Jogador que implementa Serializable.
 * Representa um jogador em um jogo de trivia, armazenando informações como nome, data de início do jogo,
 * perguntas respondidas corretamente e incorretamente.
 */
public class Jogador implements Serializable{
    private String nome;
    private LocalDateTime dataInicioJogo;
    private ArrayList<Pergunta> perguntasCertas = new ArrayList<Pergunta>();
    private ArrayList<Pergunta> perguntasErradas = new ArrayList<Pergunta>();

    /**
     * Construtor para a classe Jogador.
     *
     * @param nome              Nome do jogador.
     * @param dataInicioJogo    Data e hora de início do jogo.
     * @param perguntasCertas   Lista de perguntas que o jogador respondeu corretamente.
     * @param perguntasErradas  Lista de perguntas que o jogador respondeu incorretamente.
     */
    public Jogador(String nome, LocalDateTime dataInicioJogo, ArrayList<Pergunta> perguntasCertas, ArrayList<Pergunta> perguntasErradas) {
        this.nome = nome;
        this.dataInicioJogo = dataInicioJogo;
        this.perguntasCertas = perguntasCertas;
        this.perguntasErradas = perguntasErradas;
    }
    /**
     * Retorna o nome do jogador.
     *
     * @return Nome do jogador.
     */
    public String getNome() {
        return nome;
    }
    /**
     * Retorna a data e hora de início do jogo.
     *
     * @return Data e hora de início do jogo.
     */
    public LocalDateTime getDataInicioJogo() {
        return dataInicioJogo;
    }
    /**
     * Retorna a lista de perguntas que o jogador respondeu corretamente.
     *
     * @return Lista de perguntas certas.
     */
    public ArrayList<Pergunta> getPerguntasCertas() {
        return perguntasCertas;
    }

    /**
     * Calcula a pontuação total do jogador com base nas perguntas certas.
     *
     * @param perguntasCertas Lista de perguntas respondidas corretamente pelo jogador.
     * @return Pontuação total do jogador.
     */
    protected int calcularPontuacaoTotal(ArrayList<Pergunta> perguntasCertas) {
        int pontuacaoTotal = 0;
        for (Pergunta pergunta : perguntasCertas) {
            pontuacaoTotal += pergunta.calcularPontuacao();
        }
        return pontuacaoTotal;
    }

    /**
     * @param dataHora Data e hora de início do jogo.
     * @return String com a data e hora formatada
     */
    private String formatarDataHora(LocalDateTime dataHora) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("ddMMyyyyHHmm");
        return dataHora.format(formatter);
    }


    /**
     * @param nome Nome do jogador.
     * @return String com as iniciais do nome do jogador.
     */
    private String extrairIniciais(String nome) {
        StringBuilder iniciais = new StringBuilder();
        for (String parte : nome.split("\\s+")) {
            if (!parte.isEmpty()) {
                iniciais.append(parte.charAt(0));
            }
        }
        return iniciais.toString().toUpperCase();
    }

    /**
     * @param dataHora Data e hora de início do jogo.
     * @param nomeJogador Nome do jogador.
     * @return String com o nome do ficheiro a ser criado.
     */
    private String criarNomeFicheiro(LocalDateTime dataHora, String nomeJogador) {
        String dataHoraFormatada = formatarDataHora(dataHora);
        String iniciais = extrairIniciais(nomeJogador);
        return "pootrivia_jogo_" + dataHoraFormatada + "_" + iniciais + ".dat";
    }

    /**
     * Salva os dados do jogador em um ficheiro.
     *
     * @param jogador Jogador a ser salvo.
     */
    protected void salvarDadosJogador(Jogador jogador) {
        String nomeFicheiro = criarNomeFicheiro(jogador.getDataInicioJogo(), jogador.getNome());
        File file = new File(nomeFicheiro);
        try {
            FileOutputStream fos = new FileOutputStream(file);
            ObjectOutputStream oos = new ObjectOutputStream(fos);
            oos.writeObject(jogador);
            oos.close();
            //System.out.println("Dados salvos em " + nomeFicheiro);
        } catch (FileNotFoundException ex) {
            System.out.println("Arquivo não encontrado.");
        } catch (IOException ex) {
            System.out.println("Erro ao escrever no arquivo.");
        }
    }

    /**
     * Carrega os dados de um jogador a partir de um ficheiro.
     *
     * @return Jogador com os dados carregados.
     */
   protected ArrayList<Jogador> loadObjectsFromDirectory() {
        ArrayList<Jogador> jogadorObj = new ArrayList<Jogador>();
        String directoryName = "C:/Users/andre/Documents/UC/POO/ProjetoPoo";
        File directory = new File(directoryName);

        if (directory.exists() && directory.isDirectory()) {

            File[] files = directory.listFiles((dir, name) -> name.endsWith(".dat"));
            if (files != null) {
                for (File file : files) {
                    try {
                        FileInputStream fis = new FileInputStream(file);
                        ObjectInputStream ois = new ObjectInputStream(fis);
                        Jogador jogador = (Jogador) ois.readObject();
                        jogadorObj.add(jogador);
                        //System.out.println("Objetos carregados com sucesso de " + file.getName());
                        ois.close();
                    } catch (FileNotFoundException ex) {
                        System.out.println("Arquivo não encontrado.");
                    } catch (IOException ex) {
                        System.out.println("Erro ao ler o arquivo.");
                    } catch (ClassNotFoundException ex) {
                        System.out.println("Erro a converter objeto.");
                    }
                }
            }
        } else {
            System.out.println("Diretório " + directoryName + " não encontrado ou não é um diretório.");
        }
        return jogadorObj;
    }

    /**
     * Gera e retorna uma string representando o top 3 de jogadores com base na pontuação.
     *
     * @return String representando o top 3 de jogadores.
     */
    protected String top3() { // se a pontuacao for 0 nao metemos no top3
        ArrayList<Jogador> jogadores = loadObjectsFromDirectory();
        StringBuilder top3 = new StringBuilder();
        // imprimir os 3 jogador com maior pontuação
        for (int i = 0; i < 3; i++) {
            int maiorPontuacao = 0;
            Jogador jogadorMaiorPontuacao = null;
            for (Jogador jogador : jogadores) {
                int pontuacao = calcularPontuacaoTotal(jogador.getPerguntasCertas());
                if (pontuacao > maiorPontuacao) {
                    maiorPontuacao = pontuacao;
                    jogadorMaiorPontuacao = jogador;
                }
            }
            if (jogadorMaiorPontuacao != null) {
                String data = formatarDataHora(jogadorMaiorPontuacao.getDataInicioJogo());
                top3.append(jogadorMaiorPontuacao.getNome()).append(" - ").append(data).append(" - ").append(maiorPontuacao).append("\n");
                jogadores.remove(jogadorMaiorPontuacao);
            }
        }
        //System.out.println("\nTop 3:");
        //System.out.println(top3);
        return top3.toString();
    }

    /**
     * Retorna uma representação em string do objeto Jogador.
     *
     * @return Representação em string do jogador.
     */
    @Override
    public String toString() {
        return "Jogador{" +
                "nome='" + nome + '\'' +
                ", dataInicioJogo=" + dataInicioJogo +
                ", perguntasCertas=" + perguntasCertas +
                ", perguntasErradas=" + perguntasErradas +
                '}';
    }
}
