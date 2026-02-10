package com.googol.meta1;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.InputMismatchException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

/**
 * Class cliente que comunica com o servidor via RMI para executar as operações
 * de adição de URLs, procura de palavras, procura de links que referenciam um certo url e estatisticas.
 */
public class RmiClient {

    /**
     * Apresenta o menu do programa para o cliente.
     */
    private static void menu() {
        System.out.println("╔════════════════════════════════════════════════════════════════════╗");
        System.out.println("║                           Googol  MENU                             ║");
        System.out.println("╠════════════════════════════════════════════════════════════════════╣");
        System.out.println("║ 1 - Add new URL                                                    ║");
        System.out.println("║ 2 - Search words                                                   ║");
        System.out.println("║ 3 - List of pages linked to a specific page                        ║");
        System.out.println("║ 4 - Statistics                                                     ║");
        System.out.println("║                                                                    ║");
        System.out.println("║ 9 - Show menu                                                      ║");
        System.out.println("║ 0 - Exit                                                           ║");
        System.out.println("╚════════════════════════════════════════════════════════════════════╝");
    }

     /**
     * Confirma se um URL é válido.
     * 
     * @param url URL a ser confirmado.
     * @return true se o URL for válido, caso contrário false.
     */
    private boolean isValidUrl(String url) {
        return url.startsWith("http://") || url.startsWith("https://");
    }

    /**
     * Função principal para apresentar o menu e efetuar as opções do cliente.
     * 
     * @param Gateway Interface GatewayHeader.
     * @throws Exception Em caso de falha na execução.
     */
    private void run(GatewayHeader Gateway) throws Exception {
        Scanner scanner = new Scanner(System.in);
        menu();
        while (true) {
            System.out.print("Option: ");
            int option;
            try {
                option = scanner.nextInt();
            } catch (InputMismatchException e) {
                System.err.println("Invalid option");
                scanner.next();
                continue;
            }
            scanner.nextLine();
            switch (option) {
                case 1:
                    String url;
                    do {
                        System.out.print("Insert the URL: ");
                        url = scanner.nextLine();
                        if (!isValidUrl(url)) {
                            System.err.println("Please enter a valid URL"); 
                        }
                    } while (!isValidUrl(url));

                    Gateway.sendUrlToQueue(url);
                    break;
                case 2:
                    searchWord(scanner, Gateway);
                    menu();
                    break;
                case 3:
                    String link2;
                    do {
                        System.out.print("Insert the URL: ");
                        link2 = scanner.nextLine();
                        if (!isValidUrl(link2)) {
                            System.err.println("Please enter a valid URL"); 
                        }
                    } while (!isValidUrl(link2));
                    List<String> results = new ArrayList<String>();
                    try {
                        results = Gateway.linksToUrl(link2);
                        if (results != null){
                            System.out.println("\nResults:");
                            int i = 1;
                            for (String result : results) {
                                System.out.println(i + ". " + result);
                                i++;
                            }
                            System.out.println("\n");
                        }
                    } catch (Exception e) {
                        System.err.println("Error retrieving links: " + e.getMessage());
                    }
                    menu();
                    break;
                case 4:
                    Map<String, Integer> statisticsMap = new HashMap<>();
                    statisticsMap = Gateway.readStatisticsFromFile("estatisticas.txt");
                    if (statisticsMap != null){
                        System.out.println("\nTOP 10 Searches:");
                        for (Map.Entry<String, Integer> entry : statisticsMap.entrySet()) {
                            System.out.println(entry.getKey() + ": " + entry.getValue());
                        }
                    }
                    System.out.println("\nPress Enter to return to main menu...");
                    scanner.nextLine(); 
                    menu();
                    break;
                case 9:
                    menu();
                    break;
                case 0:
                    System.out.println("GoodBye!");
                    scanner.close();
                    return;
                default:
                    System.err.println("Invalid option");
            }
        }
    }

    /**
     * Atualiza o histórico de pesquisas com os termos de pesquisa fornecidos.
     * 
     * @param searchTerms Termos de pesquisa fornecidos pelo utilizador.
     */
    private void updateSearchHistory(GatewayHeader Gateway, String searchTerms) {
        searchTerms = searchTerms.trim().toLowerCase();
        
        if (searchTerms.isEmpty()) {
            return;
        }
        
        try {
            String[] searchTermArray = searchTerms.split("\\s+");
            for (String term : searchTermArray) {
                term = term.toLowerCase();
                if (!term.isEmpty()) {
                    Gateway.updateStatistics(term);
                }
            }
        } catch (RemoteException e) {
            System.err.println("Error updating search history: " + e.getMessage());
        }
    }
    
    /**
     * Realiza a busca por palavras inseridas pelo cliente.
     * 
     * @param scanner Scanner para captura da entrada do cliente.
     * @param Gateway Interface GatewayHeader.
     * @throws IOException Caso haja erro na leitura do ficheiro.
     * @throws NotBoundException Caso o objeto RMI não esteja registado.
     */
    private void searchWord(Scanner scanner, GatewayHeader Gateway) throws IOException, NotBoundException {
        System.out.print("Enter the words to search: ");
        String words = scanner.nextLine();
        System.out.println("Searching for the words: " + words);   
        updateSearchHistory(Gateway, words);
        List<String> results = new ArrayList<String>();
        boolean connected = false;
        try {
            while (!connected) {
                try {
                    results = Gateway.searchWords(words);
                    connected = true;
                } catch (RemoteException e) {
                    Thread.sleep(1000);
                }
            }
            if (results == null || results.isEmpty()) {
                System.out.println("No results found for your search.");
                return;
            }
            int currentPage = 1;
            int maxPage = Configuration.PAGE_RESULTS;
            int totalPages = (int) Math.ceil((double) results.size() / maxPage);
            boolean viewingResults = true;
            while (viewingResults) {
                System.out.println("\nSearch Results (Page " + currentPage + " of " + totalPages + "):");
                
                int startIndex = (currentPage - 1) * maxPage;
                int endIndex = Math.min(startIndex + maxPage, results.size());
                
                for (int i = startIndex; i < endIndex; i++) {
                    try {
                        String[] urlInfo = results.get(i).split(";");
                        System.out.println((i + 1) + ".");
                        System.out.println("   Title: " + urlInfo[1]);
                        System.out.println("   Description: " + urlInfo[2]);
                        System.out.println("   URL: " + urlInfo[0] + "\n");
                    } catch (ArrayIndexOutOfBoundsException e) {
                        System.out.println("   [Result data incomplete]");
                    }
                }
                
                if (totalPages > 1) {
                    System.out.println("\nNavigation options:");
                    if (currentPage > 1) System.out.println("P - Previous page");
                    if (currentPage < totalPages) System.out.println("N - Next page");
                    System.out.println("M - Return to main menu");
                    
                    System.out.print("Option: ");
                    String navOption = scanner.nextLine().toUpperCase();
                    
                    switch (navOption) {
                        case "P":
                            if (currentPage > 1) currentPage--;
                            break;
                        case "N":
                            if (currentPage < totalPages) currentPage++;
                            break;
                        case "M":
                            viewingResults = false;
                            break;
                        default:
                            System.out.println("Invalid option. Please try again.");
                    }
                } else {
                    System.out.println("\nPress Enter to return to main menu...");
                    scanner.nextLine();
                    viewingResults = false;    
                }
            }
            
        } catch (Exception e) {
            System.err.println("Error during search: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Função main responsavel por inicializar o cliente RMI e chamar o método de execução.
     * 
     * @param args Argumentos passados para o método main.
     * @throws Exception Caso ocorra erro durante a execução do cliente.
     */
    public static void main(String[] args) throws Exception {
        boolean connected = false;
        GatewayHeader Gateway = null;
        
        while (!connected) {
            try {
                Gateway = (GatewayHeader) Naming.lookup("rmi://"+ Configuration.RMI_HOST+":"+Configuration.RMI_PORT+"/Gateway");
                connected = true;
            } catch (Exception e) {
                System.out.println("Failed to connect to the server, trying again in 3 seconds");
                Thread.sleep(3000);
            }
        }

        RmiClient client = new RmiClient();
        try {
            client.run(Gateway);
        } catch (Exception e) {
            System.err.println("Error in client execution: " + e.getMessage());
            e.printStackTrace();
            System.out.println("Restarting client in 3 seconds...");
            Thread.sleep(3000);
            main(args);
        }
    }
}