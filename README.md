# Torrenter

# Instructions to execute the torrent client

1. Open the main directory(the current directory) in your environment.


2. In the terminal, run the following command to install the dependencies.

```
pip install requirements.txt
```


3. Put your torrent file in the torrents folder.



4. Change the working directory to 'src' folder (you can use the 'cd' command)



5. Run 'async_client.py' i.e. in the terminal, with command line parameter as the torrent path


**An example:**


The torrent ubuntu.torrent exists in the torrents folder already

My current working directory is 'src' directory.

So, I will type the following command in the terminal to download that torrent:
```
python async_client.py ../torrents/ubuntu.torrent
```
