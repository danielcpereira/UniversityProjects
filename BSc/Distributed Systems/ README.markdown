# Instalação
## Para instalar e utilizar a aplicação GOOGOL, deve ter:

java
Jsoup
Ollama

# Download dos ficheiros e respetiva execução
## Comece por compilar todo o programa:

mvn clean compile

## Abra em terminais distintos:

### -URLQueue:
java -cp "googol-web\target\classes;lib\jsoup-1.18.3.jar" com.googol.meta1.URLQueue
### -Gateway:
java -cp "googol-web\target\classes;lib\jsoup-1.18.3.jar" com.googol.meta1.Gateway
### -Downloader:
java -cp "googol-web\target\classes;lib\jsoup-1.18.3.jar" com.googol.meta1.Downloader
### - os Barrels que pretender com diferentes ids:
java -cp "googol-web\target\classes;lib\jsoup-1.18.3.jar" com.googol.meta1.Barrel 1

## Execute o programa

mvn spring-boot:run

# Autores
## Daniel Coelho Pereira 2021237092
## Eduardo Luís Pereira Marques 2022231584