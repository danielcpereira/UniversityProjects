package com.googol.meta1;
import java.rmi.Remote;
import java.rmi.RemoteException;

public interface URLQueueHeader extends Remote {
    void addUrl(String url) throws RemoteException;
    String getUrl() throws RemoteException;
}