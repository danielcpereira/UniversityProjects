package com.googol.meta1;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

/**
 * Class responsável por carregar e gerir configurações do sistema a partir de um ficheiro de propriedades.
 */
public class Configuration {
    private static final Properties properties = new Properties();
    private static boolean isLoaded = false;

    public static final String RMI_HOST;
    public static final int RMI_PORT;
    public static final int DOWN_NUM;
    public static final int LINKS_NUM;
    public static final int PAGE_RESULTS;

    static {
        loadProperties();
        RMI_HOST = getProperty("rmi.server.host", "localhost");
        RMI_PORT = getIntProperty("rmi.registry.port", 1099);
        DOWN_NUM = getIntProperty("downloader.num", 5);
        LINKS_NUM = getIntProperty("links.num", 10);
        PAGE_RESULTS = getIntProperty("page.results", 10);
    }

    /**
     * Carrega as propriedades do ficheiro de propriedades.
     */
    public static void loadProperties() {
        if (!isLoaded) {
            try (FileInputStream fis = new FileInputStream("C:\\Users\\danie\\Desktop\\Googol_meta2\\googol.properties")) {
                properties.load(fis);
                isLoaded = true;
            } catch (IOException e) {
                System.err.println("Error loading the configuration file: " + e.getMessage());
            }
        }
    }

    /**
     * Obtém o valor de uma propriedade como String.
     * 
     * @param key Valor da propriedade.
     * @param defaultValue Valor padrão caso a propriedade não esteja definida.
     * @return Valor da propriedade ou o valor padrão se não existir.
     */
    public static String getProperty(String key, String defaultValue) {
        if (!isLoaded) {
            loadProperties();
        }
        return properties.getProperty(key, defaultValue);
    }

    /**
     * Obtém o valor de uma propriedade como String.
     * 
     * @param key Valor da propriedade.
     * @return Valor da propriedade ou null se não existir.
     */
    public static String getProperty(String key) {
        return getProperty(key, null);
    }

    /**
     * Obtém o valor de uma propriedade como inteiro.
     * 
     * @param key Valor da propriedade.
     * @param defaultValue Valor padrão caso a propriedade não seja válida.
     * @return Valor da propriedade convertido para inteiro ou o valor padrão.
     */
    public static int getIntProperty(String key, int defaultValue) {
        String value = getProperty(key);
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
}
