package com.googol.meta1;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.util.List;

public interface BarrelHeader extends Remote {
    void addData(String url, String title, String description, List<String> words, List<String> links) throws RemoteException;
    public List<String> searchWords(String searchWord) throws FileNotFoundException, IOException;
    public List<String> linksToUrl(String url) throws FileNotFoundException, IOException;
    boolean ping() throws RemoteException;
}