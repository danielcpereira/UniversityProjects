import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

/**
 * Classe POOTriviaApp que estende JFrame.
 * Representa a interface gráfica principal para o jogo de trivia POOTrivia.
 */
public class POOTriviaApp extends JFrame {
    private JFrame POOTriviaApp;
    private JButton botaoNovoJogo, botaoSair;

    /**
     * Construtor para a classe POOTriviaApp.
     * Configura a interface gráfica principal, incluindo botões para iniciar um novo jogo e sair.
     */
    public POOTriviaApp() {
        POOTriviaApp = this;
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(200, 125);
        JLabel menu = new JLabel("Menu", JLabel.CENTER);
        setLocationRelativeTo(null);
        botaoNovoJogo = new JButton("Jogar");
        botaoSair = new JButton("Sair");
        ButtonListener btnActionListener = new ButtonListener();
        botaoNovoJogo.addActionListener(btnActionListener);
        botaoSair.addActionListener(btnActionListener);

        JPanel painelBotoes = new JPanel(new FlowLayout(FlowLayout.CENTER));
        painelBotoes.add(botaoNovoJogo);
        painelBotoes.add(botaoSair);

        add(menu, BorderLayout.NORTH);
        add(painelBotoes, BorderLayout.CENTER);
        setVisible(true);
        painelBotoes.setVisible(true);
    }

    /**
     * Classe interna ButtonListener que implementa ActionListener.
     * Responsável por lidar com eventos de clique nos botões.
     */
    private class ButtonListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            if (e.getSource() == botaoNovoJogo) {
                POOTriviaApp.setVisible(false);
                POOTrivia trivia = new POOTrivia();
                ApresentarPergunta frame = new ApresentarPergunta(trivia.CriaPergunta());
            }
            if (e.getSource() == botaoSair) {
                POOTriviaApp.setVisible(false);
                dispose();
            }
        }
    }
}
