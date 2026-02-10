package com.googol.meta1;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.Socket;
import java.rmi.Naming;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.net.ConnectException;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;


/**
 * Class responsável por fazer o download de páginas web, processar o conteúdo e enviar os dados extraídos para o servidor RMI.
 */
public class Downloader extends Thread {
    private boolean running = true;
    private String url;
    private Document doc;
    private HashSet<String> links;
    private String words;
    private String title;
    private String data;
    private Random random = new Random(); // Para seleção aleatória de barrels

    /**
     * Construtor da classe Downloader.
     * Inicializa a lista de links e a string de palavras.
     */
    public Downloader() {
        this.links = new HashSet<String>();
        this.words = "";
    }

    /**
     * Encontra todos os barrels disponíveis no Registry RMI e retorna um aleatoriamente.
     * 
     * @return Nome do serviço barrel encontrado ou null se nenhum for encontrado.
     */
    private String findAvailableBarrel() {
        try {
            Registry registry = LocateRegistry.getRegistry(Configuration.RMI_HOST, Configuration.RMI_PORT);
            String[] services = registry.list();

            List<String> barrelServices = new ArrayList<>();
            for (String service : services) {
                if (service.startsWith("Barrel")) {
                    barrelServices.add(service);
                }
            }
            
            if (barrelServices.isEmpty()) {
                System.out.println("No barrels found in registry.");
                return null;
            }

            int randomIndex = random.nextInt(barrelServices.size());
            String selectedBarrel = barrelServices.get(randomIndex);
            System.out.println("Barrel randomly selected: " + selectedBarrel);
            return selectedBarrel;
            
        } catch (Exception e) {
            System.err.println("Error searching for available barrels: " + e.getMessage());
            return null;
        }
    }
    
    /**
     * Processa o download da página, extrai os links, título e palavras-chave e envia os dados para o servidor.
     * 
     * @param queue Fila de URLs.
     */
    private void process_download(URLQueueHeader queue) {
        String title = doc.title();
        String description = "";
        
        try {
            title = doc.title();
            this.title = title;
            Element descriptionElement = doc.select("meta[name=description]").first();
            if (descriptionElement != null) {
                description = descriptionElement.attr("content");
            } 
        } catch (NullPointerException e) {
            return;
        }
    
        String[] wordsArray = doc.text().toLowerCase().split(" ");
        List<String> cleanedWords = new ArrayList<>();
    
        for (String word : wordsArray) {

            // \\p{Punct} -> todos os sinais de pontuação
            // \\p{Sc} -> todos os símbolos de moeda
            // \\p{Sm} -> todos os símbolos matemáticos
            // \\p{So} -> todos os símbolos de outros tipos

            word = word.replaceAll("[\\p{Punct}\\p{Sc}\\p{Sm}\\p{So}]", "").toLowerCase();
            
            if (!word.isEmpty()) {
                cleanedWords.add(word);
            }
        }
    
        int count = 0;
        Elements links = doc.select("a[href]");
        for (Element link : links) {
            String url = link.attr("abs:href");
            this.links.add(url);
            try {
                queue.addUrl(url);
            } catch (Exception e) {
                System.err.println("Failed to send the URL to the queue via RMI: " + e.getMessage());
            }
            count++;
            if (count == Configuration.LINKS_NUM) {
                break;
            }
        }
        

        boolean dataSent = false;
        int maxRetries = 3;
        int retries = 0;
        
        while (!dataSent && retries < maxRetries) {
            try {
                String barrelName = findAvailableBarrel();
                if (barrelName == null) {
                    System.err.println("Unable to find an available barrel. Attempt " + (retries + 1) + " of " + maxRetries);
                    retries++;
                    Thread.sleep(1000);
                    continue;
                }
                
                String rmiUrl = "rmi://" + Configuration.RMI_HOST + ":" + Configuration.RMI_PORT + "/" + barrelName;
                System.out.println("Trying to connect to barrel: " + rmiUrl);
                
                BarrelHeader barrel = (BarrelHeader) Naming.lookup(rmiUrl);
                List<String> linkList = new ArrayList<>(this.links);
                barrel.addData(this.url, this.title, description, cleanedWords, linkList);
                
                System.out.println("Data sent to " + barrelName + " successfully.");
                dataSent = true;
            } catch (Exception e) {
                System.err.println("Failed to send data to barrel: " + e.getMessage());
                retries++;
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        
        if (!dataSent) {
            System.err.println("Failed to send data after " + maxRetries + " attempts.");
        }
    }
    
    /**
     * Função executada quando a thread é iniciada. Obtém URLs da fila, faz o download do conteúdo e processa as informações.
     * Lida com erros de conexão e falhas no download.
     * 
     * @throws RuntimeException Caso ocorra um erro durante a execução.
     */
    public void run() throws RuntimeException {
        try {
            URLQueueHeader queue = (URLQueueHeader) Naming.lookup("rmi://"+ Configuration.RMI_HOST+":"+Configuration.RMI_PORT+"/URLQueue");
            while (running) {
                clear();
                this.url = queue.getUrl();
                if (this.url == null) {
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                    continue;
                }
                try {
                    System.out.println("Downloading: " + this.url);
                    this.doc = Jsoup.connect(this.url).get();
                } catch (ConnectException e) {
                    System.out.println("Downloader failed to connect to URL: " + this.url);
                    continue;
                } catch (Exception e) {
                    System.err.println("Downloader failed to download URL: " + this.url);
                    continue;
                }
                process_download(queue);
            }
        } catch (Exception e) {
            System.err.println("Downloader failed: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Limpa os dados armazenados.
     */
    private void clear() {
        this.links.clear();
        this.words = "";
        this.data = "";
    }
    
    /**
     * Método main para iniciar um único downloader.
     */
    public static void main(String[] args) {
        try {
            Downloader downloader = new Downloader();
            downloader.start();
            System.out.println("Downloader iniciado");
            
        } catch (Exception e) {
            System.err.println("Erro ao iniciar o downloader: " + e.getMessage());
            e.printStackTrace();
        }
    }
}